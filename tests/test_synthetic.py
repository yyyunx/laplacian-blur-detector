"""Seeded image generation and capture/split provenance."""

import csv
import json

import cv2
import numpy as np
from pathlib import Path

from laplacian_blur_detector.synthetic import CASES, generate_dataset, preview_image

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_synthetic_inputs_and_labels_are_reproducible_without_split_leakage(tmp_path):
    first = generate_dataset(tmp_path / "one", seed=7, samples_per_case=2)
    second = generate_dataset(tmp_path / "two", seed=7, samples_per_case=2)
    assert first.read_bytes() == second.read_bytes()
    with first.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 24 and {row["reason"] for row in rows} == set(CASES)
    assert {row["group"] for row in rows if row["split"] == "test"}.isdisjoint({row["group"] for row in rows if row["split"] == "calibration"})
    for row in rows:
        assert (first.parent / row["filename"]).read_bytes() == (second.parent / row["filename"]).read_bytes()
    metadata = read_json(first.parent / "dataset.json")
    assert metadata["generator_version"] == 1
    assert "not_human" in metadata["evidence"]


def test_browser_fixture_matches_generated_preview():
    bundled = cv2.imread(str(Path(__file__).resolve().parents[1] / 'web/demo.png'), cv2.IMREAD_GRAYSCALE)
    np.testing.assert_array_equal(bundled, preview_image())
