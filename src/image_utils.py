"""Safe image-loading helpers used by the CLI and dataset tools."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def load_image(path: str | Path) -> np.ndarray:
    """Load a supported image without changing the source file."""
    image_path = Path(path)
    if not image_path.is_file():
        raise FileNotFoundError(f"Image file does not exist: {image_path}")
    if image_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValueError("Unsupported image format. Use JPG, JPEG, or PNG.")
    if image_path.stat().st_size == 0:
        raise ValueError(f"Image file is empty: {image_path}")

    image = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"Could not decode image: {image_path}")
    return image


def decode_image_bytes(data: bytes, filename: str | None = None) -> np.ndarray:
    """Decode uploaded JPG, JPEG, or PNG bytes into an OpenCV image."""
    if filename and Path(filename).suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValueError("Unsupported image format. Use JPG, JPEG, or PNG.")
    if not data:
        raise ValueError("Image upload is empty.")

    encoded = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError("Could not decode uploaded image.")
    return image
