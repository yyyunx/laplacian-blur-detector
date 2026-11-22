# Core and local HTTP API reference

Import the public functions from `laplacian_blur_detector`. The new measurements
also live in `laplacian_blur_detector.sharpness`. Importing the core requires only
NumPy and OpenCV; it does not require FastAPI, Uvicorn, Pillow, or browser code.

## Existing interfaces

```python
calculate_blur_score(image: np.ndarray) -> float
detect_blur(image: np.ndarray, threshold: float) -> BlurDetectionResult
```

These retain their existing implementation and input behavior. The first returns
`float(cv2.Laplacian(gray, cv2.CV_64F).var())`. The second returns exactly
`blur_score`, `threshold`, and `is_blurry`, with `is_blurry = blur_score < threshold`.
Thresholds must be finite and non-negative; equality passes. Existing `src`
compatibility imports continue to delegate to these functions. No texture flag
is added to these legacy results, so their behavior on flat images is unchanged.

## Whole-image measurements

```python
SharpnessMetric = Literal["laplacian", "tenengrad"]

calculate_sharpness(
    image: np.ndarray,
    metric: SharpnessMetric = "laplacian",
) -> float

calculate_tenengrad_score(image: np.ndarray) -> float
```

Metric names are case-sensitive. `calculate_tenengrad_score(image)` is equivalent
to `calculate_sharpness(image, metric="tenengrad")`. Both return measurements
without applying a threshold or making a blur decision.

The new functions accept non-empty grayscale `(H, W)` or `(H, W, 1)` arrays with
dtype `uint8`, `uint16`, `float32`, or `float64`. OpenCV BGR `(H, W, 3)` and BGRA
`(H, W, 4)` arrays support `uint8`, `uint16`, or `float32`; OpenCV does not convert
float64 color arrays. Convert those explicitly to a supported dtype first.
Inputs use OpenCV BGR order, not RGB. Grayscale conversion uses `cv2.cvtColor`
for color inputs, ignores alpha, and preserves the original intensity scale.
Grayscale values must be finite. Derivatives use float64 to avoid unsigned
overflow and support floating-point grayscale inputs. Images are not modified.

| Metric | Exact computation after grayscale conversion |
| --- | --- |
| `laplacian` | `cv2.Laplacian(gray64, cv2.CV_64F).var()`; default kernel size 1 |
| `tenengrad` | `mean(gx**2 + gy**2)`, where `gx = cv2.Sobel(gray64, cv2.CV_64F, 1, 0, ksize=3)` and `gy = cv2.Sobel(gray64, cv2.CV_64F, 0, 1, ksize=3)` |

Both use OpenCV's default `scale=1`, `delta=0`, and `BORDER_DEFAULT`
(`BORDER_REFLECT_101`). Tenengrad here is mean squared gradient magnitude over
**all** pixels, with no gradient threshold, square root, normalization, or
pre-smoothing. It is mean energy, rather than a sum that grows with pixel count.
For uint8/uint16 images, new Laplacian scores
match `calculate_blur_score()` without changing that function's implementation.

## Local sharpness analysis

```python
analyze_local_sharpness(
    image: np.ndarray,
    grid_size: int | tuple[int, int] = (8, 8),
    metric: SharpnessMetric = "laplacian",
    *,
    min_texture_std: float = 5.0,
) -> list[LocalSharpnessResult]
```

`grid_size` is a count of cells: an integer specifies a square grid, and a tuple
specifies `(rows, columns)`. Both counts must be positive integers, no greater
than the corresponding image dimension. A too-large grid is rejected rather
than producing empty cells or silently changing the requested grid.

For row `r` and column `c`, bounds are:

```python
y0, y1 = r * H // rows, (r + 1) * H // rows
x0, x1 = c * W // columns, (c + 1) * W // columns
cell = gray[y0:y1, x0:x1]
```

This includes every pixel exactly once, even when dimensions are not divisible
by the grid counts. Results are in row-major order and use Python scalar values:

| Field | Type | Meaning |
| --- | --- | --- |
| `row`, `column` | `int` | Zero-based grid indices |
| `x`, `y` | `int` | Top-left pixel coordinates, with origin at image top-left |
| `width`, `height` | `int` | Cell dimensions; exclusive end is `(x + width, y + height)` |
| `metric` | `SharpnessMetric` | Selected metric name |
| `sharpness_score` | `float` | Variance (Laplacian) or mean energy (Tenengrad) of this cell's full-image response |
| `texture_std` | `float` | Population standard deviation of grayscale crop intensities |
| `is_low_texture` | `bool` | `texture_std <= min_texture_std` |

`min_texture_std` must be a finite non-negative number. Its units match image
intensity: the default `5.0` is intended for a 0–255 scale, not normalized 0–1
floats or a full 16-bit scale. Change it explicitly for those inputs. A perfectly
constant cell remains flagged even with a cutoff of zero.

Low-texture cells retain their numeric score for inspection; no score is replaced
with zero or omitted. The flag means there is little intensity variation to
support a blur assessment, not that the crop is blurry. It cannot distinguish
uniform content from severe blur. Standard deviation is only a contrast proxy:
a smooth gradient can have high standard deviation without fine detail. A false
flag does not certify sharpness, texture sufficiency, or measurement confidence.
No `is_blurry` field or universal acceptance threshold is provided.

Derivatives are computed on the **full grayscale image once**, and each cell
then takes variance of the Laplacian response or mean of the Sobel energy within
its bounds. Reflection is applied only at the outer image perimeter. This avoids
artificial crop-border responses and preserves real edges across grid lines.
A pixel's derivative may use immediate neighboring pixels outside its cell;
texture standard deviation still uses only pixels inside the cell. A constant
cell next to a real edge can therefore have a nonzero response and a low-texture
flag. A 1×1 Laplacian cell has zero variance; its Tenengrad energy need not be zero.
Tenengrad cell means aggregate to the whole-image mean when weighted by area;
Laplacian cell variances generally do not. A single cell agrees with the global
metric. Grid size and content must be held consistent when comparing scores.

This corrects the unreleased Phase 1 crop-first implementation: local numeric
scores near grid boundaries can change. Function signatures, record fields,
whole-image functions, and all legacy detector consumers remain compatible.

Whole-image scoring runs in O(H×W) time; local analysis also runs in O(H×W), plus
one scoring operation per cell. Very fine grids add overhead and weaken the
evidence in each cell. Processing uses full-image float64 grayscale storage and
temporary derivative arrays; no models, caches, network calls, or file IO occur.

## Errors and interpretation

New functions raise `ValueError` for invalid/empty image arrays, unsupported
shapes/dtypes, non-finite grayscale values, or unknown metric names. Local
analysis also raises `ValueError` for invalid grids and texture cutoffs.

Scores from Laplacian and Tenengrad **cannot be compared directly**, and thresholds
must not be transferred between them. Both depend on contrast, scene content,
noise, compression, resizing, intensity scale, and preprocessing. Noise may raise
a score without improving useful detail; low scores may reflect flat content.
They are neither probabilities nor complete image-quality assessments. Even
within one metric, comparisons require controlled conditions and representative
calibration. The texture flag does not remove these limitations.

## Local HTTP API

`POST /api/sharpness/local` accepts multipart form fields:

| Field | Default | Contract |
| --- | --- | --- |
| `image` | Required | Still JPEG/PNG, same validation as `/api/blur/check` |
| `metric` | `laplacian` | `laplacian` or `tenengrad`, case-sensitive |
| `grid_rows`, `grid_columns` | `8` each | Integers from 1 to 32; at most 1,024 total cells |
| `min_texture_std` | `5.0` | Finite non-negative cutoff in native grayscale units |

Both `height // grid_rows` and `width // grid_columns` must be at least `16`.
Small images can use a smaller grid; images under 16 pixels on either axis cannot
use the local endpoint. These service limits do not restrict the offline library.

The response has `success`, `filename`, `width`, `height`, `file_size`, `metric`,
`grid_rows`, `grid_columns`, `min_texture_std`, `coordinate_space`, `processing_ms`,
and `cells` (the `LocalSharpnessResult` records defined above). There is no
`is_blurry`, confidence, or normalized score. JPEG/PNG EXIF rotation/mirroring is
applied after shared decoding for this endpoint; `coordinate_space` is
`exif_oriented_pixels`. Width, height, and cell coordinates refer to that oriented
image, matching the browser preview. Python array callers control orientation
themselves. Legacy endpoints retain their original decoding/orientation behavior.

The endpoint reuses the bounded upload reader, header checks before decoding,
decoded pixel limit, request-stream limiter, worker thread pool, and the same
analysis semaphore as the blur endpoints. The slot is held through orientation,
full-image derivatives, and cell statistics, and released on every failure.
Files are closed on completion or error. Default limits are 10 MiB per file,
20 million pixels, 1 MiB multipart overhead, and two analyses per server process.

| HTTP status / `error_code` | Meaning |
| --- | --- |
| 400 / `INVALID_METRIC` | Unknown metric |
| 400 / `INVALID_GRID` | Grid counts outside 1–32 |
| 400 / `GRID_TOO_FINE` | At least one cell dimension would be below 16 pixels |
| 400 / `INVALID_TEXTURE_CUTOFF` | Negative or non-finite cutoff |
| 400 / existing image codes | Invalid, empty, animated, or unsupported image |
| 413 / existing size codes | File, pixels, or streamed request exceeds limits |
| 422 | Missing or malformed multipart fields, including non-integer grids |
| 503 / `SERVICE_BUSY` | All shared slots occupied; `Retry-After: 1` |

`GET /api/config` adds a `local_sharpness` object with `default_grid_size: 8`,
`max_grid_size: 32`, `max_cells: 1024`, and `min_cell_size: 16`. All previous config
keys are retained. `/api/blur/check` and `/api/blur/batch` retain their exact
response fields, thresholds, and decisions. CLI and benchmark policy formats
remain unchanged. See the [HTTP usage reference](../README.md#browser-tool-and-api)
or `/docs` on the running optional server for OpenAPI documentation.

## Browser heatmap mapping

The SVG overlay uses the local endpoint cells directly. The browser maps raw
scores of **non-low-texture cells in the current image/metric/grid** linearly:
`relative = (score - minimum) / (maximum - minimum)`, clamped to 0–1. Colors run
blue → teal → yellow. Low-texture cells are excluded from the range and use a
separate hatch. Equal eligible scores receive midpoint color (`0.5`); when all
cells are low texture, the color scale is unavailable. Raw scores remain visible
on hover, tap, or keyboard inspection. Relative values are display values only,
not cross-image normalized scores or blur probabilities. Noise, edge content,
outliers, and grid changes can affect the range; an image may receive a bright
cell even if all its regions have weak detail. No blur localization is claimed.

The browser's **Try generated demo** button loads the bundled synthetic PNG
locally, so interactive inspection does not require a native file chooser.
The fixture is generated by `synthetic.preview_image()` and contains no external
images. Benchmark CLI and frozen policy contracts are documented separately in
[BENCHMARKING.md](BENCHMARKING.md).
