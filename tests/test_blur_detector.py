"""Tests for blur scoring, file validation, and the HTTP API."""

from __future__ import annotations

import cv2
import numpy as np
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from api.main import app
from src.blur_detector import calculate_blur_score, detect_blur
from src.config import DEFAULT_BLUR_THRESHOLD
from src.image_utils import load_image


def synthetic_sharp_image() -> np.ndarray:
    """Create an image with many crisp edges."""
    image = np.zeros((160, 160, 3), dtype=np.uint8)
    for coordinate in range(0, 160, 20):
        cv2.line(image, (coordinate, 0), (coordinate, 159), (255, 255, 255), 2)
        cv2.line(image, (0, coordinate), (159, coordinate), (255, 255, 255), 2)
    cv2.putText(image, "IR", (46, 94), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 180, 255), 2)
    return image


def encode_png(image: np.ndarray) -> bytes:
    """Encode an image for an API upload test."""
    success, encoded = cv2.imencode(".png", image)
    assert success
    return encoded.tobytes()


def test_clear_synthetic_image_scores_higher_than_blurred_version() -> None:
    sharp = synthetic_sharp_image()
    blurred = cv2.GaussianBlur(sharp, (15, 15), 0)
    assert calculate_blur_score(sharp) > calculate_blur_score(blurred)


def test_threshold_classification() -> None:
    image = synthetic_sharp_image()
    score = calculate_blur_score(image)
    assert detect_blur(image, score + 1)["is_blurry"] is True
    assert detect_blur(image, score)["is_blurry"] is False


def test_grayscale_image_is_supported() -> None:
    grayscale = cv2.cvtColor(synthetic_sharp_image(), cv2.COLOR_BGR2GRAY)
    assert calculate_blur_score(grayscale) > 0


def test_invalid_image_input_raises_clear_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="NumPy array"):
        calculate_blur_score(None)  # type: ignore[arg-type]

    invalid = tmp_path / "not-an-image.txt"  # type: ignore[operator]
    invalid.write_text("not an image", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported"):
        load_image(invalid)


def test_healthz() -> None:
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_web_demo_is_served() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Laplacian Blur Detector" in response.text


def test_blur_check_api() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/blur/check",
        files={"image": ("sharp.png", encode_png(synthetic_sharp_image()), "image/png")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["filename"] == "sharp.png"
    assert payload["width"] == 160
    assert payload["height"] == 160
    assert payload["file_size"] > 0
    assert payload["threshold"] == DEFAULT_BLUR_THRESHOLD
    assert isinstance(payload["blur_score"], float)
    assert isinstance(payload["is_blurry"], bool)


def test_blur_check_api_accepts_custom_threshold() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/blur/check",
        data={"threshold": "120"},
        files={"image": ("sharp.png", encode_png(synthetic_sharp_image()), "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["threshold"] == 120.0


def test_blur_check_api_rejects_invalid_upload() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/blur/check", files={"image": ("bad.txt", b"not image", "text/plain")}
    )
    assert response.status_code == 400
