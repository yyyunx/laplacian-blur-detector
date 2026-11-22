"""Diagnostic definitions, native sharpness reuse and opt-in hint semantics."""

from dataclasses import asdict

import cv2
import numpy as np
import pytest

from laplacian_blur_detector import (
    DiagnosticPolicy, calculate_sharpness, diagnose_image_quality, measure_image_quality,
)


def test_hand_computed_measurements_and_native_sharpness():
    image = np.array([[0, 16, 128, 250, 255]], dtype=np.uint8)
    result = measure_image_quality(image)
    assert result["brightness"]["mean"] == pytest.approx(129.8 / 255)
    assert result["brightness"]["median"] == 128 / 255
    assert result["exposure"]["dark_pixel_ratio"] == 2 / 5
    assert result["exposure"]["bright_pixel_ratio"] == 2 / 5
    assert result["resolution"] == {"width": 5, "height": 1, "pixels": 5}
    for metric in ("laplacian", "tenengrad"):
        assert result["sharpness"][metric + "_score"] == calculate_sharpness(image, metric)


def test_dtype_scaling_is_explicit_and_not_per_image_minmax():
    image = np.array([[0, 16, 128, 250, 255]], dtype=np.uint8)
    original = measure_image_quality(image)
    wide = measure_image_quality(image.astype(np.uint16) * 257)
    normalized = measure_image_quality(image.astype(np.float64) / 255)
    for result in (wide, normalized):
        assert result["brightness"]["mean"] == pytest.approx(original["brightness"]["mean"])
        assert result["exposure"]["dark_pixel_ratio"] == original["exposure"]["dark_pixel_ratio"]
        assert result["exposure"]["bright_pixel_ratio"] == original["exposure"]["bright_pixel_ratio"]
    assert wide["sharpness"]["tenengrad_score"] == pytest.approx(original["sharpness"]["tenengrad_score"] * 257**2)
    assert measure_image_quality(np.full((8, 8), 128, dtype=np.uint16))["brightness"]["mean"] == pytest.approx(128 / 65535)


def test_bright_pixel_measurement_detects_saturated_color_and_ignores_alpha():
    red = np.full((8, 8, 4), (0, 0, 255, 0), dtype=np.uint8)
    result = measure_image_quality(red)
    assert result["brightness"]["mean"] == pytest.approx(76 / 255)
    assert result["exposure"]["bright_pixel_ratio"] == 1
    black = np.full((8, 8, 4), (0, 0, 0, 255), dtype=np.uint8)
    assert measure_image_quality(black)["exposure"]["bright_pixel_ratio"] == 0


def test_default_policy_measures_without_a_universal_acceptance_gate():
    result = diagnose_image_quality(np.zeros((16, 16), dtype=np.uint8))
    assert not any(check["status"] == "warning" for check in result["checks"].values())
    assert result["checks"]["brightness"]["status"] == "not_evaluated"
    assert result["checks"]["sharpness"]["status"] == "insufficient_evidence"
    assert result["policy"] == asdict(DiagnosticPolicy())
    assert "is_blurry" not in result and "accepted" not in result
    assert all(check["limitation"] for check in result["checks"].values())


def test_dark_capture_suggestions_and_low_texture_do_not_reject_for_sharpness():
    policy = DiagnosticPolicy(min_mean_brightness=0.2, max_dark_ratio=0.5,
                              min_width=32, min_height=32, min_laplacian_score=100,
                              min_tenengrad_score=10000, sharpness_intensity_max=255)
    result = diagnose_image_quality(np.zeros((16, 16), dtype=np.uint8), policy)
    for name in ("brightness", "underexposure", "resolution"):
        assert result["checks"][name]["status"] == "warning"
        assert result["checks"][name]["suggestion"]
    assert result["checks"]["sharpness"]["status"] == "insufficient_evidence"
    assert "flat content" in result["checks"]["sharpness"]["suggestion"]


def test_bright_capture_and_resolution_boundaries():
    image = np.full((17, 15), 255, dtype=np.uint8)
    policy = DiagnosticPolicy(max_bright_ratio=0.1, min_width=15, min_height=17)
    result = diagnose_image_quality(image, policy)
    assert result["checks"]["overexposure"]["status"] == "warning"
    assert "lighting angle" in result["checks"]["overexposure"]["suggestion"]
    assert result["checks"]["resolution"]["status"] == "within_policy"
    equality = diagnose_image_quality(image, DiagnosticPolicy(max_bright_ratio=1, min_mean_brightness=1))
    assert equality["checks"]["overexposure"]["status"] == "within_policy"
    assert equality["checks"]["brightness"]["status"] == "within_policy"


def test_sharpness_uses_independent_calibrated_limits_with_focus_suggestion():
    y, x = np.indices((128, 128))
    sharp = (((x // 8 + y // 8) % 2) * 255).astype(np.uint8)
    blurred = cv2.GaussianBlur(sharp, (15, 15), 3)
    limits = {"min_" + metric + "_score": (calculate_sharpness(sharp, metric) + calculate_sharpness(blurred, metric)) / 2
              for metric in ("laplacian", "tenengrad")}
    policy = DiagnosticPolicy(**limits, sharpness_intensity_max=255)
    assert diagnose_image_quality(sharp, policy)["checks"]["sharpness"]["status"] == "within_policy"
    check = diagnose_image_quality(blurred, policy)["checks"]["sharpness"]
    assert check["status"] == "warning" and "refocusing" in check["suggestion"]
    with pytest.raises(ValueError, match="dtype scale"):
        diagnose_image_quality(sharp.astype(np.uint16), policy)


def test_invalid_policies_are_rejected_without_silent_coercion():
    for value in ({"unknown": 1}, {"max_dark_ratio": 1.1}, {"max_bright_ratio": float("nan")},
                  {"min_mean_brightness": True}, {"min_width": 2.5}, {"min_height": 0},
                  {"dark_pixel_cutoff": 0.9, "bright_pixel_cutoff": 0.1},
                  {"min_laplacian_score": 100}, {"sharpness_intensity_max": 100},
                  {"min_tenengrad_score": float("inf")}, {"max_dark_ratio": "0.5"},
                  {"min_laplacian_score": 10**400}):
        with pytest.raises(ValueError):
            DiagnosticPolicy.from_mapping(value)
    with pytest.raises(ValueError, match="object"):
        DiagnosticPolicy.from_mapping([])


def test_invalid_images_and_float_color_range_are_rejected():
    for image in (None, np.zeros((0, 8), dtype=np.uint8), np.full((8, 8), np.nan),
                  np.full((8, 8), 1.1), np.full((8, 8, 3), (0, 0, 2), dtype=np.float32)):
        with pytest.raises(ValueError):
            diagnose_image_quality(image)


def test_input_is_not_modified():
    image = np.random.default_rng(4).integers(0, 256, (32, 32, 3), dtype=np.uint8)
    before = image.copy()
    diagnose_image_quality(image, DiagnosticPolicy.from_mapping({"max_dark_ratio": 0.5}))
    np.testing.assert_array_equal(image, before)
