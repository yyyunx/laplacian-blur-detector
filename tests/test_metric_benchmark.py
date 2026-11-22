"""Independent comparisons, transactional outputs, and calibration isolation."""

import csv
import json
import math
import xml.etree.ElementTree as ET

import pytest

from laplacian_blur_detector import benchmark
from laplacian_blur_detector.benchmark_comparison import comparison_chart
from laplacian_blur_detector.synthetic import CASES, generate_dataset

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def manifest(tmp_path):
    return generate_dataset(tmp_path / "dataset", samples_per_case=2)


def test_comparison_uses_independent_thresholds_and_replays_frozen_policies(manifest, tmp_path):
    output = tmp_path / "run"
    assert benchmark.main([str(manifest), "--compare", "--calibrate", "--output", str(output)]) == 0
    report = read_json(output / "comparison.json")
    assert len(report["rows"]) == 2
    assert {row["metric"] for row in report["rows"]} == {"laplacian", "tenengrad"}
    thresholds = []
    for metric in benchmark.METRICS:
        policy = read_json(output / metric / "policy.json")
        assert policy["metric"] == benchmark.METRICS[metric]
        thresholds.append(policy["domains"]["synthetic"])
        assert (output / metric / "latency.csv").is_file()
        summary = read_json(output / metric / "summary.json")
        timing = summary["processing_latency"]["by_domain"]["synthetic"]["test"]
        assert timing["samples"] == 12 and 0 <= timing["p50_ms"] <= timing["p95_ms"]
        assert all(math.isfinite(timing[key]) for key in ("mean_ms", "p50_ms", "p95_ms"))
    assert thresholds[0] != thresholds[1]
    assert {row["reason"] for row in report["by_reason"]} == set(CASES)
    assert ET.parse(output / "metric-comparison.svg").getroot().tag.endswith("svg")
    replay = tmp_path / "replay"
    assert benchmark.main([str(manifest), "--compare", "--policy", str(output), "--output", str(replay)]) == 0
    repeated = read_json(replay / "comparison.json")
    assert repeated["metrics"] == report["metrics"]
    def stable(rows):
        return [{key: value for key, value in row.items() if key not in {"mean_ms", "p50_ms", "p95_ms"}} for row in rows]
    assert stable(repeated["rows"]) == stable(report["rows"])


def test_test_labels_do_not_select_either_metrics_threshold(manifest, tmp_path):
    first = tmp_path / "first"
    assert benchmark.main([str(manifest), "--compare", "--calibrate", "--output", str(first)]) == 0
    with manifest.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)
    for row in rows:
        if row["split"] == "test":
            row["label"] = "usable" if row["label"] == "retake" else "retake"
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    second = tmp_path / "second"
    assert benchmark.main([str(manifest), "--compare", "--calibrate", "--output", str(second)]) == 0
    for metric in benchmark.METRICS:
        assert read_json(first / metric / "policy.json")["domains"] == read_json(second / metric / "policy.json")["domains"]


def test_comparison_failure_is_not_published_as_complete(manifest, tmp_path, monkeypatch):
    import laplacian_blur_detector.benchmark_comparison as comparison
    original = comparison.run_benchmark

    def fail_second(args):
        if args.metric == "tenengrad":
            raise ValueError("Injected second-metric failure")
        return original(args)

    monkeypatch.setattr(comparison, "run_benchmark", fail_second)
    output = tmp_path / "incomplete"
    assert benchmark.main([str(manifest), "--compare", "--calibrate", "--output", str(output)]) == 1
    assert not output.exists()
    assert not list(tmp_path.glob(".metric-comparison-*"))


def test_chart_escapes_domain_markup():
    rows = [{"metric": "laplacian", "domain": "<script>bad</script>", "mean_ms": 1,
             "balanced_accuracy": None, "threshold": 100, "samples": 2}]
    source = comparison_chart(rows)
    assert "<script>" not in source
    assert "&lt;script&gt;" in source
    ET.fromstring(source)
