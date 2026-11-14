"""End-to-end labeled reports, frozen policies, and dataset integrity."""

import csv
import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from laplacian_blur_detector.benchmark import main, read_manifest

FIELDS = ["filename", "label", "split", "group", "domain", "reason"]


def write_manifest(path: Path, rows: list[dict]) -> Path:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def dataset(root: Path, domains=("documents",)) -> tuple[Path, list[dict]]:
    rows = []
    rng = np.random.default_rng(123)
    for domain in domains:
        for split in ("calibration", "test"):
            for label in ("usable", "retake"):
                filename = f"{domain}-{split}-{label}.png"
                pixels = rng.integers(0, 256, (64, 64), dtype=np.uint8)
                if label == "retake":
                    pixels = cv2.GaussianBlur(pixels, (15, 15), 0)
                assert cv2.imwrite(str(root / filename), pixels)
                rows.append({
                    "filename": filename, "label": label, "split": split,
                    "group": f"{domain}-{split}-{label}", "domain": domain, "reason": "synthetic",
                })
    return write_manifest(root / "labels.csv", rows), rows


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_calibration_reports_per_domain_and_frozen_policy_reproduces_results(tmp_path) -> None:
    manifest, _ = dataset(tmp_path, ("documents", "products"))
    output = tmp_path / "run-one"
    assert main([str(manifest), "--calibrate", "--output", str(output)]) == 0
    policy = read_json(output / "policy.json")
    summary = read_json(output / "summary.json")
    assert set(policy["domains"]) == {"documents", "products"}
    for result in summary["by_domain"].values():
        assert result["test"]["accuracy"] == 1
        assert result["test"]["samples"] == 2
    with (output / "errors.csv").open(newline="", encoding="utf-8") as stream:
        assert list(csv.DictReader(stream)) == []
    replay = tmp_path / "run-two"
    assert main([str(manifest), "--policy", str(output / "policy.json"), "--output", str(replay)]) == 0
    replay_summary = read_json(replay / "summary.json")
    assert replay_summary["by_domain"] == summary["by_domain"]
    assert replay_summary["policy_sha256"] == summary["policy_sha256"]
    assert replay_summary["runtime_matches_policy"] is True


def test_test_labels_do_not_influence_threshold_selection(tmp_path) -> None:
    manifest, rows = dataset(tmp_path)
    first = tmp_path / "first"
    assert main([str(manifest), "--calibrate", "--output", str(first)]) == 0
    for row in rows:
        if row["split"] == "test":
            row["label"] = "retake" if row["label"] == "usable" else "usable"
    changed = write_manifest(tmp_path / "changed.csv", rows)
    second = tmp_path / "second"
    assert main([str(changed), "--calibrate", "--output", str(second)]) == 0
    assert read_json(first / "policy.json")["domains"] == read_json(second / "policy.json")["domains"]
    with (second / "errors.csv").open(newline="", encoding="utf-8") as stream:
        errors = list(csv.DictReader(stream))
    assert {row["outcome"] for row in errors} == {"false_reject", "missed_retake"}
    assert {row["split"] for row in errors} == {"test"}


@pytest.mark.parametrize("field,value,match", [
    ("filename", "../escape.png", "inside"),
    ("filename", "C:/private/photo.png", "inside"),
    ("filename", "/private/photo.png", "inside"),
    ("label", "maybe", "label"),
    ("split", "train", "split"),
    ("group", "", "missing"),
])
def test_manifest_rejects_invalid_entries(tmp_path, field, value, match) -> None:
    manifest, rows = dataset(tmp_path)
    rows[0][field] = value
    write_manifest(manifest, rows)
    with pytest.raises(ValueError, match=match):
        read_manifest(manifest)


def test_capture_group_cannot_cross_calibration_and_test(tmp_path) -> None:
    manifest, rows = dataset(tmp_path)
    rows[2]["group"] = rows[0]["group"]
    write_manifest(manifest, rows)
    with pytest.raises(ValueError, match="both calibration and test"):
        read_manifest(manifest)


def test_duplicate_bytes_under_new_filename_fail_without_export(tmp_path, capsys) -> None:
    manifest, rows = dataset(tmp_path)
    source, target = (tmp_path / rows[index]["filename"] for index in (0, 2))
    target.write_bytes(source.read_bytes())
    output = tmp_path / "report"
    assert main([str(manifest), "--calibrate", "--output", str(output)]) == 1
    assert "Duplicate image bytes" in capsys.readouterr().err
    assert not output.exists()


@pytest.mark.parametrize("reuse_group", [True, False])
def test_frozen_policy_rejects_calibration_reused_as_test(tmp_path, capsys, reuse_group) -> None:
    manifest, rows = dataset(tmp_path)
    output = tmp_path / "calibrated"
    assert main([str(manifest), "--calibrate", "--output", str(output)]) == 0
    reused = [{**rows[0], "split": "test"}]
    if not reuse_group:
        reused[0]["group"] = "renamed-group"
    write_manifest(tmp_path / "reused.csv", reused)
    replay = tmp_path / "replay"
    assert main([str(tmp_path / "reused.csv"), "--policy", str(output / "policy.json"), "--output", str(replay)]) == 1
    assert "overlaps the policy calibration" in capsys.readouterr().err
    assert not replay.exists()


def test_existing_report_is_not_overwritten(tmp_path, capsys) -> None:
    manifest, _ = dataset(tmp_path)
    output = tmp_path / "report"
    assert main([str(manifest), "--calibrate", "--output", str(output)]) == 0
    original = (output / "summary.json").read_bytes()
    assert main([str(manifest), "--threshold", "0", "--output", str(output)]) == 1
    assert "new directory" in capsys.readouterr().err
    assert (output / "summary.json").read_bytes() == original


def test_corrupt_image_is_not_silently_excluded_from_metrics(tmp_path, capsys) -> None:
    manifest, rows = dataset(tmp_path)
    (tmp_path / rows[0]["filename"]).write_bytes(b"not an image")
    output = tmp_path / "report"
    assert main([str(manifest), "--calibrate", "--output", str(output)]) == 1
    assert "Could not decode" in capsys.readouterr().err
    assert not output.exists()


@pytest.mark.parametrize("change", ["metric", "nonfinite_threshold", "schema", "provenance"])
def test_incompatible_or_malformed_policy_is_rejected(tmp_path, capsys, change) -> None:
    manifest, _ = dataset(tmp_path)
    output = tmp_path / "original"
    assert main([str(manifest), "--calibrate", "--output", str(output)]) == 0
    policy = read_json(output / "policy.json")
    if change == "metric":
        policy["metric"]["preprocessing"] = "unknown"
    elif change == "nonfinite_threshold":
        policy["domains"]["documents"] = float("nan")
    elif change == "schema":
        policy["schema_version"] = 99
    else:
        del policy["calibration"]
    altered = tmp_path / "altered.json"
    altered.write_text(json.dumps(policy), encoding="utf-8")
    assert main([str(manifest), "--policy", str(altered), "--output", str(tmp_path / "new")]) == 1
    assert "Error:" in capsys.readouterr().err


def test_new_domain_cannot_silently_use_another_domains_policy(tmp_path, capsys) -> None:
    manifest, rows = dataset(tmp_path)
    output = tmp_path / "original"
    assert main([str(manifest), "--calibrate", "--output", str(output)]) == 0
    for row in rows:
        row["domain"] = "new-domain"
    write_manifest(manifest, rows)
    assert main([str(manifest), "--policy", str(output / "policy.json"), "--output", str(tmp_path / "new")]) == 1
    assert "no threshold for domain" in capsys.readouterr().err
