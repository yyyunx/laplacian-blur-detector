"""Core metric definitions, spatial analysis, and compatibility contracts."""

import subprocess
import sys

import cv2
import numpy as np
import pytest

from laplacian_blur_detector import (
    analyze_local_sharpness,
    calculate_blur_score,
    calculate_sharpness,
    calculate_tenengrad_score,
    detect_blur,
)


@pytest.fixture
def sharp_image() -> np.ndarray:
    y, x = np.indices((128, 128))
    return (((x // 4 + y // 4) % 2) * 255).astype(np.uint8)


@pytest.mark.parametrize("metric", ["laplacian", "tenengrad"])
def test_sharp_scores_higher_than_gaussian_blur(sharp_image, metric) -> None:
    blurred = cv2.GaussianBlur(sharp_image, (15, 15), 3)
    assert calculate_sharpness(sharp_image, metric) > calculate_sharpness(blurred, metric)


def test_tenengrad_is_mean_squared_gradient_energy() -> None:
    # A unit ramp has Sobel X=8 at the three interior columns and 0 at borders.
    ramp = np.tile(np.arange(5, dtype=np.uint8), (5, 1))
    assert calculate_tenengrad_score(ramp) == pytest.approx(64 * 3 / 5)
    assert calculate_tenengrad_score(ramp.T) == pytest.approx(64 * 3 / 5)
    assert calculate_tenengrad_score(ramp + ramp.T) == pytest.approx(2 * 64 * 3 / 5)


@pytest.mark.parametrize("channels", [None, 1, 3, 4])
def test_laplacian_matches_legacy_exactly(channels) -> None:
    shape = (35, 43) if channels is None else (35, 43, channels)
    image = np.random.default_rng(42).integers(0, 256, shape, dtype=np.uint8)
    expected = calculate_blur_score(image)
    assert calculate_sharpness(image) == expected
    assert calculate_sharpness(image, "laplacian") == expected
    assert detect_blur(image, expected) == {
        "blur_score": expected, "threshold": expected, "is_blurry": False,
    }


@pytest.mark.parametrize("metric", ["laplacian", "tenengrad"])
def test_local_blur_is_localized_without_changing_clear_region(sharp_image, metric) -> None:
    mixed = sharp_image.copy()
    mixed[:, 64:] = cv2.GaussianBlur(mixed[:, 64:], (15, 15), 3)
    before = analyze_local_sharpness(sharp_image, (1, 4), metric)
    after = analyze_local_sharpness(mixed, (1, 4), metric)
    assert after[0] == before[0]
    assert after[2]["sharpness_score"] < before[2]["sharpness_score"]
    assert after[0]["sharpness_score"] > after[2]["sharpness_score"]
    assert not after[0]["is_low_texture"]
    np.testing.assert_array_equal(sharp_image[:, :64], mixed[:, :64])


@pytest.mark.parametrize("metric", ["laplacian", "tenengrad"])
def test_flat_and_low_contrast_cells_are_flagged_without_blur_labels(sharp_image, metric) -> None:
    image = np.full((128, 256), 128, dtype=np.uint8)
    image[:, 128:] = 126 + (sharp_image > 0).astype(np.uint8) * 4
    flat, low_contrast = analyze_local_sharpness(image, (1, 2), metric)
    # Neighboring real edges can contribute response to a constant cell.
    assert flat["texture_std"] == 0
    assert low_contrast["sharpness_score"] > 0
    assert low_contrast["texture_std"] == 2
    for cell in (flat, low_contrast):
        assert cell["is_low_texture"] is True
        assert "is_blurry" not in cell
        assert "confidence" not in cell
    # The texture cutoff is configurable and inclusive at its boundary.
    assert analyze_local_sharpness(image, (1, 2), metric, min_texture_std=1)[1]["is_low_texture"] is False
    assert analyze_local_sharpness(image, (1, 2), metric, min_texture_std=2)[1]["is_low_texture"] is True


@pytest.mark.parametrize("metric", ["laplacian", "tenengrad"])
@pytest.mark.parametrize("grid_size", [(8, 8), (3, 7), 4])
def test_non_divisible_grid_covers_every_pixel_once(metric, grid_size) -> None:
    image = np.random.default_rng(4).integers(0, 256, (83, 97), dtype=np.uint8)
    original = image.copy()
    cells = analyze_local_sharpness(image, grid_size, metric)
    gray = image.astype(np.float64)
    if metric == "laplacian":
        response = cv2.Laplacian(gray, cv2.CV_64F)
    else:
        response = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)**2 + cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)**2
    rows, columns = (grid_size, grid_size) if isinstance(grid_size, int) else grid_size
    assert len(cells) == rows * columns
    coverage = np.zeros(image.shape, dtype=np.uint8)
    for index, cell in enumerate(cells):
        assert (cell["row"], cell["column"]) == divmod(index, columns)
        x, y, w, h = (cell[key] for key in ("x", "y", "width", "height"))
        assert w > 0 and h > 0
        crop = image[y:y + h, x:x + w]
        coverage[y:y + h, x:x + w] += 1
        region = response[y:y + h, x:x + w]
        assert cell["sharpness_score"] == (region.var() if metric == "laplacian" else region.mean())
        assert cell["texture_std"] == pytest.approx(crop.std())
        assert cell["metric"] == metric
    np.testing.assert_array_equal(coverage, np.ones(image.shape, dtype=np.uint8))
    np.testing.assert_array_equal(image, original)


@pytest.mark.parametrize("metric,expected", [("laplacian", 0), ("tenengrad", 64)])
def test_grid_boundaries_do_not_create_responses_on_linear_ramp(metric, expected) -> None:
    ramp = np.tile(np.arange(64, dtype=np.uint8), (32, 1))
    cells = analyze_local_sharpness(ramp, (1, 4), metric)
    # Interior cells have no image-perimeter reflection or artificial crop edges.
    assert cells[1]["sharpness_score"] == expected
    assert cells[2]["sharpness_score"] == expected


@pytest.mark.parametrize("metric", ["laplacian", "tenengrad"])
def test_real_edge_on_grid_line_is_preserved(metric) -> None:
    image = np.zeros((64, 64), dtype=np.uint8)
    image[:, 32:] = 255
    cells = analyze_local_sharpness(image, (1, 2), metric)
    assert all(cell["sharpness_score"] > 0 for cell in cells)
    assert all(cell["is_low_texture"] for cell in cells)


@pytest.mark.parametrize("metric", ["laplacian", "tenengrad"])
def test_single_cell_agrees_with_global_metric(sharp_image, metric) -> None:
    assert analyze_local_sharpness(sharp_image, 1, metric)[0]["sharpness_score"] == calculate_sharpness(sharp_image, metric)


def test_default_grid_and_one_pixel_cells(sharp_image) -> None:
    assert analyze_local_sharpness(sharp_image) == analyze_local_sharpness(sharp_image, (8, 8))
    assert len(analyze_local_sharpness(sharp_image)) == 64
    for metric in ("laplacian", "tenengrad"):
        cell = analyze_local_sharpness(np.array([[128]], dtype=np.uint8), 1, metric)[0]
        assert (cell["x"], cell["y"], cell["width"], cell["height"]) == (0, 0, 1, 1)
        assert cell["sharpness_score"] == 0
        assert cell["is_low_texture"] is True


@pytest.mark.parametrize("channels", [1, 3, 4])
def test_tenengrad_uses_opencv_grayscale_and_ignores_alpha(channels) -> None:
    image = np.random.default_rng(12).integers(0, 256, (32, 40, channels), dtype=np.uint8)
    gray = image[:, :, 0] if channels == 1 else cv2.cvtColor(
        image, cv2.COLOR_BGR2GRAY if channels == 3 else cv2.COLOR_BGRA2GRAY,
    )
    assert calculate_tenengrad_score(image) == calculate_tenengrad_score(gray)
    assert analyze_local_sharpness(image) == analyze_local_sharpness(gray)


@pytest.mark.parametrize("dtype", [np.uint8, np.uint16, np.float32, np.float64])
def test_grayscale_dtypes_preserve_intensity_scale(sharp_image, dtype) -> None:
    assert calculate_tenengrad_score(sharp_image.astype(dtype)) == calculate_tenengrad_score(sharp_image)
    floating = sharp_image.astype(dtype).astype(np.float64)
    assert calculate_tenengrad_score(floating * 2) == pytest.approx(calculate_tenengrad_score(floating) * 4)


@pytest.mark.parametrize("function", [calculate_sharpness, calculate_tenengrad_score, analyze_local_sharpness])
@pytest.mark.parametrize("image,match", [
    (None, "NumPy array"),
    (np.zeros((0, 10), dtype=np.uint8), "empty"),
    (np.zeros((10, 0, 3), dtype=np.uint8), "empty"),
    (np.zeros((10,), dtype=np.uint8), "grayscale"),
    (np.zeros((10, 10, 2), dtype=np.uint8), "channels"),
    (np.zeros((10, 10), dtype=np.int64), "dtype"),
    (np.full((10, 10), np.nan), "finite"),
    (np.full((10, 10), np.inf), "finite"),
])
def test_invalid_images_raise_value_error(function, image, match) -> None:
    with pytest.raises(ValueError, match=match):
        function(image)


@pytest.mark.parametrize("function", [calculate_sharpness, analyze_local_sharpness])
@pytest.mark.parametrize("metric", ["unknown", "Tenengrad", None])
def test_unknown_metric_is_rejected(sharp_image, function, metric) -> None:
    with pytest.raises(ValueError, match="Metric"):
        function(sharp_image, metric=metric)


@pytest.mark.parametrize("grid", [0, -1, True, 2.5, (), (2,), (2, 3, 4), [2, 3], (2, 0), (True, 2), (2, 1.5), (129, 1), (1, 129)])
def test_invalid_or_oversized_grids_are_rejected(sharp_image, grid) -> None:
    with pytest.raises(ValueError, match="Grid"):
        analyze_local_sharpness(sharp_image, grid)


@pytest.mark.parametrize("cutoff", [-1, float("nan"), float("inf"), None, "bad"])
def test_invalid_texture_cutoff_is_rejected(sharp_image, cutoff) -> None:
    with pytest.raises(ValueError, match="texture std"):
        analyze_local_sharpness(sharp_image, min_texture_std=cutoff)


def test_core_import_and_measurements_do_not_require_server_dependencies() -> None:
    subprocess.run([sys.executable, "-c", """
import sys
for dependency in ('fastapi', 'uvicorn', 'PIL', 'starlette'):
    sys.modules[dependency] = None
import numpy as np
from laplacian_blur_detector import calculate_tenengrad_score, analyze_local_sharpness
image = np.zeros((16, 16), dtype=np.uint8)
assert calculate_tenengrad_score(image) == 0
assert len(analyze_local_sharpness(image)) == 64
"""], check=True, timeout=30)


@pytest.mark.parametrize("dtype", [np.uint8, np.uint16, np.float32, np.float64])
def test_native_storage_matches_float64_reference_without_mutating_input(dtype):
    from laplacian_blur_detector.sharpness import _prepare_grayscale

    image = np.random.default_rng(42).integers(0, 256, (133, 149), dtype=np.uint16).astype(dtype)
    if dtype == np.uint16:
        image *= 251
    original = image.copy()
    reference = image.astype(np.float64)
    for metric in ("laplacian", "tenengrad"):
        assert calculate_sharpness(image, metric) == calculate_sharpness(reference, metric)
        assert analyze_local_sharpness(image, (3, 5), metric) == analyze_local_sharpness(reference, (3, 5), metric)
    assert np.array_equal(image, original)
    if dtype in (np.uint8, np.uint16):
        assert np.shares_memory(_prepare_grayscale(image), image)
