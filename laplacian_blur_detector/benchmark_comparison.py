"""Compare existing benchmark runs; calibration and policy logic stay in benchmark."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from html import escape
from pathlib import Path
import tempfile

from .benchmark import METRICS, _canonical_json, _write_csv, load_policy, run_benchmark
from .evaluation import classification_metrics

COMPARISON_COLUMNS = [
    "metric", "domain", "threshold", "samples", "balanced_accuracy", "retake_precision",
    "retake_recall", "retake_f1", "false_reject_rate", "missed_retake_rate",
    "mean_ms", "p50_ms", "p95_ms",
]
LIMITATIONS = [
    "Scores and thresholds have metric-specific units; never transfer a raw threshold between metrics.",
    "Retake is the positive class. Undefined rates are null, not perfect scores.",
    "Noise can raise either score; low texture can lower it without blur. Partial blur may be hidden by global detail.",
    "Latency is a single-pass decode plus measurement, without warmup, file IO, hashing, or report writing. It is hardware/load dependent.",
    "Synthetic labels demonstrate behavior only; they do not establish real-world accuracy.",
]


def comparison_chart(rows: list[dict]) -> str:
    """Dependency-free SVG with separately scaled quality and latency panels."""
    height = 138 + len(rows) * 95
    peak = max((row["mean_ms"] for row in rows), default=1) or 1
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 {height}" role="img" aria-labelledby="title desc">',
             '<title id="title">Held-out metric comparison</title>',
             '<desc id="desc">Balanced accuracy and mean processing latency with metric-specific thresholds. Synthetic results are not real-world accuracy.</desc>',
             f'<rect width="1000" height="{height}" fill="#0b1120"/>',
             '<g font-family="sans-serif" fill="#f3f7ff">',
             '<text x="28" y="35" font-size="24">Held-out metric comparison</text>',
             '<text x="28" y="60" font-size="14" fill="#aabbd2">Independent thresholds · retake = positive · same manifest and splits</text>',
             '<text x="320" y="91" font-size="14">Balanced accuracy (0–1)</text>',
             '<text x="680" y="91" font-size="14">Mean decode + metric latency (ms)</text>']
    for index, row in enumerate(rows):
        y = 120 + index * 95
        label = escape(f"{row['metric']} / {row['domain']}")
        quality = row["balanced_accuracy"]
        parts.extend([
            f'<text x="28" y="{y}" font-size="16">{label}</text>',
            f'<text x="28" y="{y + 23}" font-size="13" fill="#aabbd2">threshold {row["threshold"]:.6g} · n={row["samples"]}</text>',
            f'<rect x="320" y="{y - 15}" width="260" height="20" fill="#24334b" rx="3"/>',
            f'<rect x="680" y="{y - 15}" width="220" height="20" fill="#24334b" rx="3"/>',
            f'<rect x="680" y="{y - 15}" width="{220 * row["mean_ms"] / peak:.3f}" height="20" fill="#71b7ff" rx="3"/>',
            f'<text x="910" y="{y}" font-size="14">{row["mean_ms"]:.3f}</text>',
        ])
        if quality is not None:
            parts.append(f'<rect x="320" y="{y - 15}" width="{260 * quality:.3f}" height="20" fill="#72d3b2" rx="3"/>')
        parts.append(f'<text x="590" y="{y}" font-size="14">{"N/A" if quality is None else f"{quality:.3f}"}</text>')
    parts.extend([f'<text x="28" y="{height - 20}" font-size="13" fill="#aabbd2">Synthetic experiments are not real-world validation. Latency varies with hardware and load; see comparison.json.</text>', '</g></svg>'])
    return "\n".join(parts) + "\n"


def _read_predictions(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def run_comparison(args: argparse.Namespace) -> dict:
    """Reuse run_benchmark once per metric, then publish one complete new directory."""
    output = args.output
    if output.exists():
        raise ValueError("Output must be a new directory; choose a new run name.")
    if not args.calibrate and not args.policy:
        raise ValueError("Comparison requires independent calibration or frozen policies.")
    if args.policy:
        for metric in METRICS:
            load_policy(args.policy / metric / "policy.json", metric)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".metric-comparison-", dir=output.parent) as temporary:
        stage = Path(temporary) / "report"
        stage.mkdir()
        rows, conditions, descriptors = [], [], {}
        fingerprints = None
        manifest_hash = None
        runtime_warnings = []
        for metric in METRICS:
            run_args = argparse.Namespace(**vars(args))
            run_args.metric, run_args.compare, run_args.output = metric, False, stage / metric
            run_args.policy = args.policy / metric / "policy.json" if args.policy else None
            summary = run_benchmark(run_args)
            descriptors[metric] = {"metric": summary["metric"], "policy_sha256": summary["policy_sha256"]}
            if not summary["runtime_matches_policy"]:
                runtime_warnings.append(f"{metric}: runtime differs from frozen policy.")
            predictions = _read_predictions(run_args.output / "predictions.csv")
            current_fingerprints = [(r["filename"], r["sha256"], r["label"], r["split"], r["domain"]) for r in predictions]
            if fingerprints is not None and (current_fingerprints != fingerprints or summary["manifest_sha256"] != manifest_hash):
                raise ValueError("Dataset changed between metrics; no comparison was published.")
            fingerprints, manifest_hash = current_fingerprints, summary["manifest_sha256"]
            for domain, result in summary["by_domain"].items():
                test = result["test"]
                latency = summary["processing_latency"]["by_domain"][domain]["test"]
                rows.append({"metric": metric, "domain": domain, "threshold": result["threshold"],
                             **{key: test[key] for key in COMPARISON_COLUMNS[3:10]},
                             **{key: latency[key] for key in ("mean_ms", "p50_ms", "p95_ms")}})
                reasons = sorted({r["reason"] for r in predictions if r["domain"] == domain and r["split"] == "test" and r["reason"]})
                for reason in reasons:
                    selected = [r for r in predictions if r["domain"] == domain and r["split"] == "test" and r["reason"] == reason]
                    conditions.append({"metric": metric, "domain": domain, "reason": reason,
                                       **classification_metrics([float(r["blur_score"]) for r in selected], [r["label"] for r in selected], result["threshold"])})
        report = {
            "schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
            "scope": "held_out_test", "positive_class": "retake", "manifest_sha256": manifest_hash,
            "metrics": descriptors, "runtime": summary["runtime"],
            "environment": summary["environment"],
            "latency_scope": summary["processing_latency"]["scope"],
            "warnings": runtime_warnings, "limitations": LIMITATIONS, "rows": rows, "by_reason": conditions,
        }
        (stage / "comparison.json").write_text(_canonical_json(report), encoding="utf-8")
        _write_csv(stage / "comparison.csv", COMPARISON_COLUMNS, rows)
        (stage / "metric-comparison.svg").write_text(comparison_chart(rows), encoding="utf-8")
        (stage / "README.txt").write_text(
            "Held-out metric comparison; positive class is retake.\n"
            "Each metric subdirectory contains its own frozen policy, predictions, errors, latency, and summary.\n"
            + "\n".join(LIMITATIONS + runtime_warnings) + "\n", encoding="utf-8",
        )
        if output.exists():
            raise ValueError("Output appeared during evaluation; choose a new run name.")
        stage.rename(output)
    return report
