# Image quality diagnostics

Diagnostics are measurements and configurable hints, not an overall image-quality
score or acceptance gate. The core depends only on NumPy/OpenCV and reuses the
existing sharpness functions; it has no HTTP, storage, or browser dependency.

```python
from laplacian_blur_detector import (
    DiagnosticPolicy, measure_image_quality, diagnose_image_quality,
)

measurements = measure_image_quality(image)
report = diagnose_image_quality(image)  # Measurements only; warning rules disabled.
policy = DiagnosticPolicy.from_mapping({
    "min_mean_brightness": 0.2,
    "max_dark_ratio": 0.5,
    "max_bright_ratio": 0.2,
    "min_width": 640,
    "min_height": 480,
})
report = diagnose_image_quality(image, policy)
```

The numbers above are uncalibrated examples, not recommended universal thresholds.
Choose bounds for the capture task and representative images. `None` disables a
warning rule. Default pixel cutoffs define measured intensity regions and do not
enable pass/fail rules.

## Measurement definitions

- Brightness: mean and median OpenCV grayscale encoded intensity, normalized by
  dtype range (`255` for uint8, `65535` for uint16). No per-image min/max stretch.
  Float grayscale/BGR inputs must already be finite in 0–1. Inputs follow the
  existing sharpness shape/dtype contracts; float64 color conversion is unsupported.
- Dark ratio: grayscale pixels **at or below** `dark_pixel_cutoff` (default 16/255),
  divided by all pixels.
- Bright ratio: pixels with **any non-alpha color channel at or above**
  `bright_pixel_cutoff` (default 250/255), divided by all pixels. Grayscale uses its
  single channel. This preserves information about saturated colors that a
  grayscale-only bright check would miss.
- Resolution: array width, height, and pixel count. Width/height limits are
  directional; callers control orientation before passing an array.
- Sharpness: existing Laplacian variance and Tenengrad energy, in **native input
  intensity units**, plus grayscale texture standard deviation (native and
  normalized). Alpha is ignored, including hidden RGB values in transparent pixels.

Encoded intensity is not physical luminance. Dark backgrounds, white backgrounds,
and saturated colors can be intentional; ratios cannot prove camera underexposure
or sensor clipping. Pixel count does not establish useful detail. Noise, contrast,
resizing, content and compression affect sharpness. These limits are included in
each diagnostic report.

## Policy and suggestions

`DiagnosticPolicy` accepts these fields (unknown fields and non-finite values fail):

| Field | Default | Meaning |
| --- | --- | --- |
| `dark_pixel_cutoff`, `bright_pixel_cutoff` | 16/255, 250/255 | Normalized intensity cutoffs; dark must be below bright |
| `min_texture_std` | 5/255 | Normalized grayscale std cutoff for insufficient evidence |
| `min_mean_brightness` | None | Warn below this normalized mean |
| `max_dark_ratio`, `max_bright_ratio` | None | Warn above the specified ratio |
| `min_width`, `min_height` | None | Warn below these positive integer dimensions |
| `min_laplacian_score`, `min_tenengrad_score` | None | Independently calibrated native sharpness limits |
| `sharpness_intensity_max` | None | Required scale pin for sharpness limits: 1, 255, or 65535 |

All normalized fields must be finite in 0–1. Booleans/numeric strings are not
accepted as numeric policy values. Sharpness limits cannot reuse thresholds across
metrics or bit depths; a mismatched explicit scale pin is rejected. Equality meets
warning bounds; texture std equal to its cutoff is insufficient evidence.

Reports contain `schema_version`, `measurements`, the complete resolved `policy`,
`checks`, and overall `limitations`. Each check has `status`, `message`,
`suggestion`, and `limitation`. Status values are `not_evaluated`, `within_policy`,
`warning`, `informational`, or `insufficient_evidence`. Within-policy means only
that the explicitly configured bound was met. There is no `accepted`, `is_blurry`,
or overall quality-pass field.

Configured warnings suggest more lighting, reviewing exposure/lighting angle,
higher-resolution capture, or refocusing/stabilizing the camera, as appropriate.
Low texture suppresses sharpness warnings in favor of insufficient evidence and
an inspection suggestion; it does not suppress unrelated brightness/resolution
hints. It never directly rejects an image. Grayscale std is a contrast proxy,
not proof of useful texture.
