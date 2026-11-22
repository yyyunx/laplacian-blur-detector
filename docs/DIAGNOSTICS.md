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

## Independent HTTP API

`POST /api/quality/diagnose` accepts multipart `image` plus optional `policy`
(a JSON object encoded as a string, default `{}`). A policy is capped at 8 KiB
UTF-8; duplicate/unknown fields, malformed/deep JSON, booleans in numeric fields,
and non-finite values are rejected. The complete resolved policy is returned.

```bash
curl -X POST http://127.0.0.1:8000/api/quality/diagnose -F "image=@sample.jpg" -F 'policy={"min_width":640,"max_dark_ratio":0.5}'
```

The response includes the core report plus `success`, `filename`, `width`,
`height`, `file_size`, `processing_ms`, and `coordinate_space` set to
`exif_oriented_pixels`. JPEG/PNG EXIF orientation is applied before measurements,
so minimum dimensions refer to the displayed orientation. No heatmap grid is
required; tiny images can be measured and assessed against an explicit policy.

The endpoint shares encoded-file, header/pixel, streaming-body limits, the worker
thread pool, analysis semaphore, EXIF transform, and upload cleanup with existing
analysis. Policy parsing happens before decode. Errors use the existing JSON
`detail`/`error_code` shape: 400 `INVALID_DIAGNOSTIC_POLICY` or
`INVALID_DIAGNOSTIC_INPUT` (including scale mismatch), 413
`DIAGNOSTIC_POLICY_TOO_LARGE` or existing upload/pixel/request limits, and 503
`SERVICE_BUSY` with `Retry-After: 1`. Missing multipart fields use 422.
All existing endpoints, including configuration, retain their prior contracts.

## Web panel and local demo

Run `laplacian-blur-serve` and open `http://127.0.0.1:8000`. Select **Try generated
demo** (or your own JPG/PNG), then **Measure quality**. The existing Original and
Heatmap views remain available for the same selected image; diagnostics has its
own request and never changes the batch decision or CSV.

The initial policy is `{}`: measurements with all warning rules disabled. Expand
**Diagnostic policy** and select **Load example hints**, customize the JSON if
needed, then measure again. This explicitly opts into uncalibrated example limits
for mean brightness, pixel ratios, and 1024×768 resolution. The generated preview
is 768×512, so it demonstrates a resolution warning and higher-resolution capture
suggestion. **Measurements only** resets the policy. No sharpness acceptance
threshold is preselected; use independently calibrated native limits if needed.

The panel reports normalized mean/median, dark/bright ratios, displayed dimensions,
both native sharpness scores, and normalized texture std. Very small nonzero values
use scientific notation instead of appearing as zero. Definitions/limitations are
collapsible. Warnings and insufficient evidence are distinct; no overall score or
pass/fail badge is provided. Images upload only on an explicit measurement request.

Policy edits, image changes, and clearing/removing a selection invalidate previous
diagnostics and cancel pending work. Generation counters discard late responses
even when abort is ignored. Batch work disables new diagnostic requests and aborts
pending ones; already accepted server work can still finish under the shared limit.
Errors/timeouts leave the original/heatmap workflow available and permit retry.

## Phase 4 validation and manual acceptance

Core/API/controller tests, builds and installed-wheel smoke checks are automated.
The final local suite contains 209 Python tests and 21 frontend tests. Each Phase 4
milestone runs the Windows/Ubuntu × Python 3.10/3.12/3.13 CI matrix before proceeding.
No benchmark labels or data were changed and no accuracy gain is claimed.

Actual browser QA remains **not completed**. On the Phase 4 review attempt,
rebinding the existing localhost tab timed out after kernel reinitialization.
Retries stopped; desktop/mobile rendering, pointer interactions and visual EXIF
alignment must still be accepted manually. No browser screenshot is claimed.

Manual checklist (retain the existing [heatmap checklist](VALIDATION.md#repeat-the-pending-visual-checks)):

1. At desktop width (1280px) and phone width (390px), use **Try generated demo**.
   Verify Original/Heatmap switching, both metrics, opacity 0/55/100 and cell hover,
   tap/keyboard information, with no horizontal control overflow.
2. Measure quality with `{}`: numeric measurements must appear, without universal
   warning/pass rules. Load the example policy and measure again: dimensions
   768×512 must trigger the explicitly configured 1024×768 resolution warning.
3. On a dark image, enable mean/dark-ratio limits and inspect lighting suggestions;
   on a white/saturated image enable bright-ratio hints. Do not interpret them as
   proof of sensor clipping. On flat content, sharpness must be insufficient
   evidence even with explicit sharpness limits, not directly rejected.
4. Upload portrait/landscape and odd-size images plus EXIF rotations/mirrors.
   Quality dimensions and heatmap coordinates must match the displayed orientation.
5. Rapidly switch images, edit policy, clear the queue, and start/cancel/retry a
   batch while requests are pending. Old hints/maps must never repaint a new
   selection; quality settings must not change batch thresholds/counts/CSV.
6. Enter invalid/duplicate JSON fields and wrong sharpness intensity scale. Verify
   readable errors, cleared stale results and successful correction/retry.
