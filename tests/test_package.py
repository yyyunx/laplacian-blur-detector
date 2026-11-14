"""Public package, compatibility, and CLI regression coverage."""

import csv

import cv2
import numpy as np

from laplacian_blur_detector import calculate_blur_score, detect_blur
from laplacian_blur_detector.cli import main as check_image
from laplacian_blur_detector.evaluate import main as evaluate
from src.blur_detector import calculate_blur_score as legacy_score


def test_legacy_import_delegates_to_public_package() -> None:
    assert legacy_score is calculate_blur_score
    assert detect_blur(np.zeros((16, 16), dtype=np.uint8), 100)["is_blurry"]


def test_image_cli_reports_result(tmp_path, capsys) -> None:
    image = tmp_path / "sample.png"
    assert cv2.imwrite(str(image), np.zeros((16, 16), dtype=np.uint8))
    assert check_image([str(image), "--threshold", "120"]) == 0
    output = capsys.readouterr().out
    assert "Threshold: 120.00" in output
    assert "Result: BLURRY" in output


def test_image_cli_reports_missing_input(tmp_path, capsys) -> None:
    assert check_image([str(tmp_path / "missing.png")]) == 1
    assert "does not exist" in capsys.readouterr().err


def test_evaluation_exports_valid_images_and_reports_corrupt_files(tmp_path, capsys) -> None:
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    assert cv2.imwrite(str(dataset / "sample.png"), np.zeros((16, 16), dtype=np.uint8))
    (dataset / "broken.png").write_bytes(b"not an image")
    output = tmp_path / "results" / "scores.csv"
    assert evaluate([str(dataset), "--output", str(output)]) == 0
    with output.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    assert rows[0]["filename"] == "sample.png"
    assert rows[0]["is_blurry"] == "True"
    assert "broken.png" in capsys.readouterr().err
