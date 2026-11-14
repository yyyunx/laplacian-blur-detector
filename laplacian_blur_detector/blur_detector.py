"""Core image-blur detection based on Laplacian variance."""

from __future__ import annotations

from typing import TypedDict

import cv2
import numpy as np


class BlurDetectionResult(TypedDict):
    """The result returned by :func:`detect_blur`."""

    blur_score: float
    threshold: float
    is_blurry: bool


def _to_grayscale(image: np.ndarray) -> np.ndarray:
    """Validate an OpenCV image and return a grayscale view/copy as needed."""
    if not isinstance(image, np.ndarray):
        raise ValueError("Image must be a NumPy array.")
    if image.size == 0:
        raise ValueError("Image must not be empty.")
    if image.ndim == 2:
        return image
    if image.ndim != 3:
        raise ValueError("Image must be grayscale, BGR, or BGRA.")

    channels = image.shape[2]
    if channels == 1:
        return image[:, :, 0]
    if channels == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if channels == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    raise ValueError("Image must have 1, 3, or 4 channels.")


def calculate_blur_score(image: np.ndarray) -> float:
    """Return the variance of the grayscale image's Laplacian response."""
    gray = _to_grayscale(image)
    try:
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())
    except cv2.error as error:
        raise ValueError(f"Could not calculate blur score: {error}") from error


def detect_blur(image: np.ndarray, threshold: float) -> BlurDetectionResult:
    """Score an image and classify it as blurry when score is below threshold."""
    try:
        resolved_threshold = float(threshold)
    except (TypeError, ValueError) as error:
        raise ValueError("Threshold must be a finite non-negative number.") from error
    if not np.isfinite(resolved_threshold) or resolved_threshold < 0:
        raise ValueError("Threshold must be a finite non-negative number.")

    score = calculate_blur_score(image)
    return {
        "blur_score": score,
        "threshold": resolved_threshold,
        "is_blurry": score < resolved_threshold,
    }
