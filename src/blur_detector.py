"""Compatibility imports; new integrations should use laplacian_blur_detector.blur_detector."""

from laplacian_blur_detector.blur_detector import (
    BlurDetectionResult,
    calculate_blur_score,
    detect_blur,
)

__all__ = ['BlurDetectionResult', 'calculate_blur_score', 'detect_blur']
