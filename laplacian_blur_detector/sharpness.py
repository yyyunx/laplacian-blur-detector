"""NumPy/OpenCV sharpness measurements without application-level decisions."""

from __future__ import annotations

from numbers import Integral
from typing import Literal, TypedDict

import cv2
import numpy as np

from .blur_detector import _to_grayscale

SharpnessMetric = Literal["laplacian", "tenengrad"]


class LocalSharpnessResult(TypedDict):
    """One grid cell; coordinates describe image[y:y+height, x:x+width]."""

    row: int
    column: int
    x: int
    y: int
    width: int
    height: int
    metric: SharpnessMetric
    sharpness_score: float
    texture_std: float
    is_low_texture: bool


def _validate_metric(metric: SharpnessMetric) -> None:
    if metric not in ("laplacian", "tenengrad"):
        raise ValueError("Metric must be 'laplacian' or 'tenengrad'.")


def _prepare_grayscale(image: np.ndarray) -> np.ndarray:
    # Keep legacy input validation and conversion semantics without changing them.
    try:
        gray = _to_grayscale(image)
    except cv2.error as error:
        raise ValueError(f"Could not convert image to grayscale: {error}") from error
    if gray.dtype not in (np.uint8, np.uint16, np.float32, np.float64):
        raise ValueError("Image dtype must be uint8, uint16, float32, or float64.")
    if np.issubdtype(gray.dtype, np.floating):
        if not np.isfinite(gray).all():
            raise ValueError("Image values must be finite.")
        # OpenCV's CV_64F derivatives support float64, not every float32 path.
        return gray.astype(np.float64, copy=False)
    # Preserve integer storage: CV_64F derivative outputs still avoid overflow.
    # Integer values are always finite; no whole-image float64 copy is needed.
    return gray


def _response(gray: np.ndarray, metric: SharpnessMetric) -> np.ndarray:
    if metric == "laplacian":
        return cv2.Laplacian(gray, cv2.CV_64F)
    gradient_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gradient_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    np.square(gradient_x, out=gradient_x)
    np.square(gradient_y, out=gradient_y)
    gradient_x += gradient_y
    return gradient_x


def _statistic(response: np.ndarray, metric: SharpnessMetric) -> float:
    return float(response.var() if metric == "laplacian" else response.mean())


def calculate_sharpness(
    image: np.ndarray, metric: SharpnessMetric = "laplacian",
) -> float:
    """Return Laplacian variance or mean squared 3x3 Sobel gradient magnitude.

    Intensities are not normalized. Scores from different metrics, intensity
    scales, resolutions, or content are not directly comparable. No threshold or
    blur classification is applied. See docs/API.md for the full input contract.
    """
    _validate_metric(metric)
    return _statistic(_response(_prepare_grayscale(image), metric), metric)


def calculate_tenengrad_score(image: np.ndarray) -> float:
    """Return mean(Sobel_x**2 + Sobel_y**2), with 3x3 unscaled Sobel kernels."""
    return calculate_sharpness(image, metric="tenengrad")


def _grid_shape(grid_size: int | tuple[int, int], height: int, width: int) -> tuple[int, int]:
    if isinstance(grid_size, Integral) and not isinstance(grid_size, (bool, np.bool_)):
        rows, columns = grid_size, grid_size
    elif isinstance(grid_size, tuple) and len(grid_size) == 2:
        rows, columns = grid_size
    else:
        raise ValueError("Grid size must be a positive integer or a (rows, columns) tuple.")
    if any(
        not isinstance(value, Integral) or isinstance(value, (bool, np.bool_)) or value <= 0
        for value in (rows, columns)
    ):
        raise ValueError("Grid rows and columns must be positive integers.")
    if rows > height or columns > width:
        raise ValueError("Grid rows and columns must not exceed image height and width.")
    return int(rows), int(columns)


def analyze_local_sharpness(
    image: np.ndarray,
    grid_size: int | tuple[int, int] = (8, 8),
    metric: SharpnessMetric = "laplacian",
    *,
    min_texture_std: float = 5.0,
) -> list[LocalSharpnessResult]:
    """Measure non-overlapping cells of a full-image response in row-major order.

    Grid size is a cell count, not a pixel size. Integer division assigns all
    pixels, including remainders. Derivatives use reflected borders only at the
    image perimeter, never at grid boundaries. A cell with grayscale std <=
    min_texture_std is flagged
    as low texture; this is a heuristic, not a blur decision or confidence score.
    The default texture cutoff uses native 0..255 intensity units.
    """
    _validate_metric(metric)
    gray = _prepare_grayscale(image)
    height, width = gray.shape
    rows, columns = _grid_shape(grid_size, height, width)
    try:
        texture_cutoff = float(min_texture_std)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("Minimum texture std must be a finite non-negative number.") from error
    if not np.isfinite(texture_cutoff) or texture_cutoff < 0:
        raise ValueError("Minimum texture std must be a finite non-negative number.")

    results: list[LocalSharpnessResult] = []
    response = _response(gray, metric)
    for row in range(rows):
        y0, y1 = row * height // rows, (row + 1) * height // rows
        for column in range(columns):
            x0, x1 = column * width // columns, (column + 1) * width // columns
            cell = gray[y0:y1, x0:x1]
            texture_std = float(cell.std())
            results.append({
                "row": row, "column": column,
                "x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0,
                "metric": metric,
                "sharpness_score": _statistic(response[y0:y1, x0:x1], metric),
                "texture_std": texture_std,
                "is_low_texture": texture_std <= texture_cutoff,
            })
    return results
