"""Labeled dataset evaluation with frozen policies and held-out reporting."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import platform
import sys
from time import perf_counter

import cv2
import numpy as np

from . import __version__
from .blur_detector import calculate_blur_score
from .config import DEFAULT_BLUR_THRESHOLD
from .evaluation import calibrate_threshold, classification_metrics, finite_nonnegative
from .image_utils import decode_image_bytes
from .sharpness import calculate_tenengrad_score

METRIC = {"name": "laplacian_variance", "version": 1, "preprocessing": "opencv_grayscale_native_v1"}
METRICS = {
    "laplacian": METRIC,
    "tenengrad": {
        "name": "tenengrad", "version": 1,
        "preprocessing": "opencv_grayscale_native_float64_sobel3_energy_mean_v1",
    },
}
REQUIRED_COLUMNS = {"filename", "label", "split", "group", "domain"}
PREDICTION_COLUMNS = [
    "filename", "domain", "group", "split", "label", "reason", "sha256",
    "blur_score", "threshold", "prediction", "outcome",
]


@dataclass(frozen=True)
class Sample:
    filename: str
    path: Path
    label: str
    split: str
    group: str
    domain: str
    reason: str


@dataclass(frozen=True)
class ScoredSample:
    sample: Sample
    score: float
    sha256: str
    processing_ms: float = 0.0


def read_manifest(manifest: Path, image_root: Path | None = None, *, content: bytes | None = None) -> list[Sample]:
    """Validate labels, unique files, containment, and capture-group isolation."""
    root = (image_root or manifest.parent).resolve()
    samples: list[Sample] = []
    paths: set[Path] = set()
    groups: dict[str, str] = {}
    data = manifest.read_bytes() if content is None else content
    with io.StringIO(data.decode("utf-8-sig"), newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        fields = reader.fieldnames or []
        if not REQUIRED_COLUMNS.issubset(fields) or len(fields) != len(set(fields)):
            raise ValueError(f"Manifest needs unique columns: {', '.join(sorted(REQUIRED_COLUMNS))}.")
        for line, row in enumerate(reader, start=2):
            if None in row or any(not row.get(key, "") or not row[key].strip() for key in REQUIRED_COLUMNS):
                raise ValueError(f"Manifest row {line}: missing values or extra CSV fields.")
            values = {key: value.strip() if value else "" for key, value in row.items()}
            filename = values["filename"].replace("\\", "/")
            relative = PurePosixPath(filename)
            if relative.is_absolute() or PureWindowsPath(filename).drive or ".." in relative.parts:
                raise ValueError(f"Manifest row {line}: filename must stay inside the image root.")
            path = (root / filename).resolve()
            if not path.is_relative_to(root):
                raise ValueError(f"Manifest row {line}: filename must stay inside the image root.")
            if path in paths:
                raise ValueError(f"Manifest row {line}: duplicate image path {filename!r}.")
            paths.add(path)
            if values["label"] not in {"usable", "retake"}:
                raise ValueError(f"Manifest row {line}: label must be usable or retake.")
            if values["split"] not in {"calibration", "test"}:
                raise ValueError(f"Manifest row {line}: split must be calibration or test.")
            group, split = values["group"], values["split"]
            if group in groups and groups[group] != split:
                raise ValueError(f"Capture group {group!r} occurs in both calibration and test splits.")
            groups[group] = split
            samples.append(Sample(
                filename, path, values["label"], split, group, values["domain"], values.get("reason", ""),
            ))
    if not samples:
        raise ValueError("Manifest contains no samples.")
    for domain in {sample.domain for sample in samples}:
        if not any(sample.domain == domain and sample.split == "test" for sample in samples):
            raise ValueError(f"Domain {domain!r} needs held-out test samples.")
    return samples


def score_samples(samples: list[Sample], metric: str = "laplacian") -> list[ScoredSample]:
    if metric not in METRICS:
        raise ValueError("Unsupported benchmark metric.")
    scored: list[ScoredSample] = []
    hashes: dict[str, str] = {}
    for sample in samples:
        try:
            data = sample.path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            if digest in hashes:
                raise ValueError(f"Duplicate image bytes: {sample.filename!r} and {hashes[digest]!r}.")
            hashes[digest] = sample.filename
            started = perf_counter()
            image = decode_image_bytes(data, sample.filename)
            measure = calculate_blur_score if metric == "laplacian" else calculate_tenengrad_score
            score = finite_nonnegative(measure(image))
            processing_ms = (perf_counter() - started) * 1000
        except (OSError, ValueError, cv2.error) as error:
            raise ValueError(f"Cannot evaluate {sample.filename!r}: {error}") from error
        scored.append(ScoredSample(sample, score, digest, processing_ms))
    return scored


def _canonical_json(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


def load_policy(path: Path, metric: str | None = "laplacian") -> dict:
    policy = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(policy, dict) or type(policy.get("schema_version")) is not int or policy["schema_version"] != 1:
        raise ValueError("Unsupported policy schema; expected schema_version 1.")
    allowed = list(METRICS.values()) if metric is None else [METRICS[metric]]
    descriptor = policy.get("metric")
    if not isinstance(descriptor, dict) or type(descriptor.get("version")) is not int or descriptor not in allowed:
        raise ValueError("Policy metric or preprocessing is incompatible with this detector.")
    domains = policy.get("domains")
    if not isinstance(domains, dict) or not domains:
        raise ValueError("Policy must contain domain thresholds.")
    for domain, threshold in domains.items():
        if not isinstance(domain, str) or not domain.strip() or type(threshold) not in (int, float):
            raise ValueError("Policy domain thresholds must be numeric.")
        finite_nonnegative(threshold)
    calibration = policy.get("calibration")
    if not isinstance(calibration, dict):
        raise ValueError("Policy must record calibration groups and image hashes (empty for fixed policies).")
    for key in ("groups", "image_sha256"):
        values = calibration.get(key)
        if not isinstance(values, list) or any(not isinstance(value, str) or not value for value in values):
            raise ValueError(f"Policy calibration.{key} must be a list of non-empty strings.")
    _canonical_json(policy)  # Reject non-finite values even in optional metadata.
    return policy


def _new_policy(scored: list[ScoredSample], manifest_hash: str, args: argparse.Namespace) -> tuple[dict, list[dict]]:
    thresholds = {}
    candidates = []
    for domain in sorted({row.sample.domain for row in scored}):
        rows = [row for row in scored if row.sample.domain == domain and row.sample.split == "calibration"]
        if args.calibrate:
            if not rows:
                raise ValueError(f"Domain {domain!r} needs calibration samples to select a threshold.")
            threshold, curve = calibrate_threshold(
                [row.score for row in rows], [row.sample.label for row in rows],
                args.false_reject_cost, args.missed_retake_cost,
            )
            candidates.extend({"domain": domain, **point} for point in curve)
        else:
            threshold = finite_nonnegative(args.threshold)
        thresholds[domain] = threshold
    calibration = [row for row in scored if row.sample.split == "calibration"] if args.calibrate else []
    return {
        "schema_version": 1,
        "metric": METRICS[getattr(args, "metric", None) or "laplacian"],
        "detector_version": __version__,
        "runtime": {"opencv": cv2.__version__, "numpy": np.__version__},
        "selection": {
            "mode": "calibrated" if args.calibrate else "fixed",
            "objective": "weighted_class_error" if args.calibrate else None,
            "false_reject_cost": args.false_reject_cost if args.calibrate else None,
            "missed_retake_cost": args.missed_retake_cost if args.calibrate else None,
            "tie_break": "fewer_missed_retakes_then_lower_threshold" if args.calibrate else None,
        },
        "domains": thresholds,
        "calibration": {
            "manifest_sha256": manifest_hash if args.calibrate else None,
            "groups": sorted({row.sample.group for row in calibration}),
            "image_sha256": sorted({row.sha256 for row in calibration}),
        },
    }, candidates


def _check_policy_test_isolation(policy: dict, scored: list[ScoredSample]) -> None:
    groups = set(policy["calibration"]["groups"])
    hashes = set(policy["calibration"]["image_sha256"])
    for row in scored:
        if row.sample.domain not in policy["domains"]:
            raise ValueError(f"Policy has no threshold for domain {row.sample.domain!r}.")
        if row.sample.split == "test" and (row.sample.group in groups or row.sha256 in hashes):
            raise ValueError(f"Test sample {row.sample.filename!r} overlaps the policy calibration data.")


def _write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def run_benchmark(args: argparse.Namespace) -> dict:
    """Validate everything before exclusively creating a new report directory."""
    output = args.output
    if output.exists():
        raise ValueError("Output must be a new directory; choose a new run name.")
    manifest_data = args.manifest.read_bytes()
    manifest_hash = hashlib.sha256(manifest_data).hexdigest()
    samples = read_manifest(args.manifest, args.image_root, content=manifest_data)
    candidates = []
    if args.policy:
        policy = load_policy(args.policy, getattr(args, "metric", None))
        metric = next(key for key, value in METRICS.items() if value == policy["metric"])
    else:
        metric = getattr(args, "metric", None) or "laplacian"
        policy = None
    args.metric = metric
    if not args.calibrate and not args.policy and args.threshold is None:
        if metric != "laplacian":
            raise ValueError("Tenengrad requires --calibrate, --policy, or its own explicit --threshold.")
        args.threshold = DEFAULT_BLUR_THRESHOLD
    scored = score_samples(samples, metric)
    if policy is None:
        policy, candidates = _new_policy(scored, manifest_hash, args)
    _check_policy_test_isolation(policy, scored)
    predictions: list[dict] = []
    for row in scored:
        sample = row.sample
        threshold = policy["domains"][sample.domain]
        prediction = "retake" if row.score < threshold else "usable"
        outcome = "correct" if prediction == sample.label else (
            "false_reject" if sample.label == "usable" else "missed_retake"
        )
        predictions.append({
            "filename": sample.filename, "domain": sample.domain, "group": sample.group,
            "split": sample.split, "label": sample.label, "reason": sample.reason,
            "sha256": row.sha256, "blur_score": row.score, "threshold": threshold,
            "prediction": prediction, "outcome": outcome,
        })
    by_domain = {}
    for domain, threshold in sorted(policy["domains"].items()):
        splits = {}
        for split in ("calibration", "test"):
            rows = [row for row in scored if row.sample.domain == domain and row.sample.split == split]
            if rows:
                splits[split] = classification_metrics(
                    [row.score for row in rows], [row.sample.label for row in rows], threshold,
                )
        if splits:
            by_domain[domain] = {"threshold": threshold, **splits}
    policy_json = _canonical_json(policy)
    summary = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "detector_version": __version__,
        "runtime": {"opencv": cv2.__version__, "numpy": np.__version__},
        "runtime_matches_policy": policy.get("runtime") == {"opencv": cv2.__version__, "numpy": np.__version__},
        "metric": METRICS[metric],
        "manifest_sha256": manifest_hash,
        "policy_sha256": hashlib.sha256(policy_json.encode("utf-8")).hexdigest(),
        "by_domain": by_domain,
        "processing_latency": {
            "scope": "decode_and_metric_only_single_pass_no_warmup",
            "unit": "ms",
            "by_domain": {
                domain: {
                    split: _latency_summary([row.processing_ms for row in scored if row.sample.domain == domain and row.sample.split == split])
                    for split in ("calibration", "test")
                    if any(row.sample.domain == domain and row.sample.split == split for row in scored)
                } for domain in by_domain
            },
        },
        "environment": {
            "python": platform.python_version(), "system": platform.system(),
            "machine": platform.machine(), "opencv_threads": cv2.getNumThreads(),
        },
    }
    summary_json = _canonical_json(summary)
    output.mkdir(parents=True)
    (output / "policy.json").write_text(policy_json, encoding="utf-8")
    (output / "summary.json").write_text(summary_json, encoding="utf-8")
    _write_csv(output / "predictions.csv", PREDICTION_COLUMNS, predictions)
    errors = [row for row in predictions if row["split"] == "test" and row["outcome"] != "correct"]
    _write_csv(output / "errors.csv", PREDICTION_COLUMNS, errors)
    _write_csv(output / "latency.csv", ["filename", "domain", "split", "processing_ms"], [
        {"filename": row.sample.filename, "domain": row.sample.domain, "split": row.sample.split, "processing_ms": row.processing_ms}
        for row in scored
    ])
    if args.calibrate:
        _write_csv(output / "thresholds.csv", [
            "domain", "threshold", "false_reject", "missed_retake", "weighted_class_error",
        ], candidates)
    return summary


def _latency_summary(values: list[float]) -> dict:
    return {
        "samples": len(values), "mean_ms": float(np.mean(values)),
        "p50_ms": float(np.percentile(values, 50)), "p95_ms": float(np.percentile(values, 95)),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate labeled image datasets on held-out samples.")
    parser.add_argument("manifest", type=Path, help="CSV with filename,label,split,group,domain and optional reason")
    parser.add_argument("--image-root", type=Path, help="Image directory (default: manifest directory)")
    parser.add_argument("--output", type=Path, default=Path("outputs/benchmark"), help="New run directory (must not already exist)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--calibrate", action="store_true", help="Select a threshold per domain using calibration rows only")
    mode.add_argument("--policy", type=Path, help="Frozen JSON policy, or prior comparison directory with --compare")
    mode.add_argument("--threshold", type=float, help="Fixed threshold (default: 100 for Laplacian only)")
    parser.add_argument("--metric", choices=tuple(METRICS), help="Metric (default: Laplacian, or infer from frozen policy)")
    parser.add_argument("--compare", action="store_true", help="Compare Laplacian and Tenengrad with independent calibrated/frozen policies")
    parser.add_argument("--false-reject-cost", type=float, help="Calibration weight for usable images rejected (default: 1)")
    parser.add_argument("--missed-retake-cost", type=float, help="Calibration weight for retake images accepted (default: 1)")
    args = parser.parse_args(argv)
    if args.compare and (args.metric or not (args.calibrate or args.policy)):
        parser.error("--compare requires --calibrate or --policy <comparison-directory>, without --metric.")
    if not args.calibrate and (args.false_reject_cost is not None or args.missed_retake_cost is not None):
        parser.error("Cost options require --calibrate.")
    args.false_reject_cost = 1.0 if args.false_reject_cost is None else args.false_reject_cost
    args.missed_retake_cost = 1.0 if args.missed_retake_cost is None else args.missed_retake_cost
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.compare:
            from .benchmark_comparison import run_comparison
            result = run_comparison(args)
            for row in result["rows"]:
                print(f"{row['metric']} / {row['domain']}: threshold={row['threshold']:.6g}, balanced_accuracy={row['balanced_accuracy']}, mean_ms={row['mean_ms']:.3f}")
            print(f"Wrote metric comparison to {args.output}")
            return 0
        summary = run_benchmark(args)
    except (OSError, ValueError, TypeError, csv.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    for domain, result in summary["by_domain"].items():
        test = result["test"]
        confusion = test["confusion"]
        print(f"{domain}: threshold={result['threshold']:.6g}, test={test['samples']}, "
              f"false_reject={confusion['false_reject']}, missed_retake={confusion['missed_retake']}")
    if not summary["runtime_matches_policy"]:
        print("Warning: runtime versions differ from the policy; compare dependency versions before reproducing results.", file=sys.stderr)
    print(f"Wrote benchmark report to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
