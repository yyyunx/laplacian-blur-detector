# Laplacian Blur Detector

![Tests](https://github.com/yyyunx/laplacian-blur-detector/actions/workflows/tests.yml/badge.svg)

A reusable image-sharpness library, command-line tool, and optional HTTP service.
The project is an open-source image quality toolkit that others can use, integrate,
and contribute to. Vehicle photos are one use case alongside document capture,
product photography, and other image upload workflows.

**Current status: early-stage, stateless toolkit.** It computes Laplacian variance;
it is not a learned model or a complete image quality assessment. Use the browser
tool, CLI, or API directly; accounts and manually labeled datasets are not required.

## Choose how to use it

| Interface | Useful for |
| --- | --- |
| Python library | Integrating measurements into your own application |
| Single-image CLI | Checking an image locally |
| Dataset CLI with CSV | Inspecting score distributions across a folder |
| Browser tool and optional API | Checking batches, exporting results, and connecting another backend |

No images are persisted by the API. The browser previews selected images locally
and uploads them only when analysis is requested. HTTP uploads may use temporary
spooled files while a request is processed; these are closed after the request.
Browser exports and the dataset CLI write CSV only when requested.

## Installation

Use Python 3.10 or newer. From a checkout of this repository:

```bash
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Choose the dependencies you need:

```bash
# Library and image/dataset CLI only
python -m pip install .

# Add the API and browser demo
python -m pip install ".[server]"

# Editable contributor setup, including API, tests, lint, and builds
python -m pip install -e ".[server,dev]"
```

These commands install from this checkout; a PyPI release is not assumed.
`python -m pip install -r requirements.txt` remains available for the complete
server/development setup. Runtime and development dependencies are declared in
`pyproject.toml`; the core library does not require FastAPI or Uvicorn.

## Python library

```python
from laplacian_blur_detector import calculate_blur_score, detect_blur
from laplacian_blur_detector.image_utils import load_image

image = load_image("sample.jpg")
score = calculate_blur_score(image)
result = detect_blur(image, threshold=100)
print(score, result)
```

The calculation is `cv2.Laplacian(gray, cv2.CV_64F).var()`. Higher scores generally
indicate more edge detail. `is_blurry` is true when the score is below the threshold;
a score exactly equal to the threshold passes. This score is not a percentage or
confidence value, and passing the threshold does not establish overall image quality.

## Command line

```bash
laplacian-blur sample.jpg --threshold 120
laplacian-blur-evaluate ./samples --output ./outputs/blur_scores.csv
```

Single-image output includes resolution, score, threshold, and CLEAR/BLURRY.
Dataset evaluation scans JPG/JPEG/PNG files recursively, reports unreadable files,
and exports `filename`, `width`, `height`, `file_size`, `blur_score`, `threshold`,
and `is_blurry`. Source images are not modified. By default the CSV is written to
`outputs/blur_scores.csv` relative to the current working directory.

Existing checkout commands remain supported:

```bash
python scripts/test_image.py sample.jpg --threshold 120
python scripts/evaluate_dataset.py ./samples
```

## Browser tool and API

Install the `server` extra, then run:

```bash
laplacian-blur-serve
```

Open the demo at <http://127.0.0.1:8000>, interactive API documentation at
<http://127.0.0.1:8000/docs>, or health check at <http://127.0.0.1:8000/healthz>.
Use `--host` and `--port` to choose the listener. The existing checkout command
`uvicorn api.main:app --host 127.0.0.1 --port 8000` also works.

Choose or drag in up to 20 JPG/JPEG/PNG images, then select **Analyze pending**.
The queue shows progress and keeps individual errors alongside successful results.
Select a filename to inspect its preview, metadata, score, and raw response.

- Filter by clear, blurry, failed, or pending; sort by filename or score.
- Cancel remaining work and resume pending images. Already completed results stay.
- Retry failed uploads without repeating successful ones.
- Export the entire queue as CSV, including failed and pending rows, in the chosen
  sort order. The filter does not remove rows from the export.
- Enter any finite non-negative threshold. Changing it invalidates previous results
  so the screen never presents decisions made with an older threshold as current.

Each browser request analyzes one image, with a 30-second client timeout. Canceling
stops further requests; work already accepted by the server may finish. No login
or image labeling is needed.

### POST /api/blur/check

Accepts multipart fields `image` and optional `threshold` (default `100.0`).

```bash
curl -X POST http://127.0.0.1:8000/api/blur/check -F "image=@sample.jpg" -F "threshold=120"
```

On Windows PowerShell, use `curl.exe` if `curl` is a shell alias.

```json
{
  "success": true,
  "filename": "sample.jpg",
  "width": 1280,
  "height": 720,
  "file_size": 862208,
  "blur_score": 184.72,
  "threshold": 120.0,
  "is_blurry": false,
  "message": "Image passes the sharpness threshold."
}
```

The message currently reflects only the blur threshold. Empty, undecodable, or
unsupported uploads and invalid non-negative finite thresholds return an error.
`GET /healthz` returns `{"status": "ok"}`.

### POST /api/blur/batch

Accepts repeated multipart `images` fields and optional `threshold`. Results keep
input order, including when filenames repeat. A bad file does not discard other results.

```bash
curl -X POST http://127.0.0.1:8000/api/blur/batch -F "images=@one.jpg" -F "images=@two.png" -F "threshold=120"
```

The response includes `total`, `processed` (successfully analyzed), `failed`, `clear`,
`blurry`, `threshold`, and `results`. Top-level `success` is false if any file failed.
Each successful row has the same fields as the single-image response, including
`processing_ms`. Failed rows contain `filename`, `success: false`, `status_code`,
`error_code`, and `message`. File-level failures use HTTP 200 for the overall batch;
invalid whole requests use an HTTP error.

### Service limits and errors

`GET /api/config` exposes the limits used by the browser:

| Limit | Default |
| --- | --- |
| Encoded size per file | 10 MiB |
| Pixels per image | 20,000,000; checked from the header before OpenCV decoding |
| Files per batch API request or browser queue | 20 |
| Combined image bytes per batch API request | 50 MiB |
| Active decodes/analyses per server process | 2 |

The browser sends sequential single-image requests, so its queue does not need to
fit into one 50 MiB multipart request. The server counts incoming body bytes even
without `Content-Length`; single/batch requests allow 1 MiB of multipart overhead
above their respective byte limit. Server processing runs in worker threads.
Supported content is still JPEG or non-animated PNG even if a file is renamed.

| Status | Meaning |
| --- | --- |
| 400 | Invalid image, unsupported format, invalid threshold, or too many batch files |
| 413 | File, dimensions, total batch, or entire request exceeds a limit |
| 422 | Missing or invalid multipart form fields |
| 503 | Analysis slots are busy; retry using the `Retry-After` hint |

Service validation errors retain the `detail` message and add `error_code`. These
bounds do not add authentication, per-client rate limits, or deployment timeouts;
see [SECURITY.md](SECURITY.md) for deployment boundaries.

## Calibration and domain-specific use

`100.0` is a development default, not a universal acceptance rule. Validate using
representative cameras, resolutions, compression levels, lighting, and subject
sizes for your use case. Record preprocessing and thresholds alongside results.

Laplacian variance measures edge detail. Noise and textured backgrounds can affect
scores; low-detail surfaces, low light, exposure problems, local blur, and small
subjects need separate evaluation. The current implementation does not normalize
resolution or color depth, select a subject region, or correct EXIF orientation.

Keep domain rules outside the measurement core. A document-scanning application
and a vehicle inspection application may use the same score with different quality
policies. For future iRent integration, a backend can call the same API before
accepting an upload; there is no dependency on iRent code.

## Contributing and project direction

Start with [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports and feature proposals
have templates, and pull requests should explain resulting behavior and validation.

- [Roadmap](docs/ROADMAP.md): usability, batch processing, stability, integration,
  and additional quality checks.
- [Architecture](docs/ARCHITECTURE.md): public interfaces and extension boundaries.
- [Changelog](CHANGELOG.md): behavior and compatibility changes.
- [Security policy](SECURITY.md): reporting and deployment boundaries.

Collaboration here means contributing code, documentation, integrations, and
reproducible fixes through GitHub. The product roadmap focuses on the image tool.

## Optional developer benchmarking

Contributors can optionally compare the detector with human judgments. This is
not required to use the image checker. Label a dataset with `filename,label,split,group,domain` (optional `reason`), then run:

```bash
laplacian-blur-benchmark data/labels.csv --calibrate --output outputs/experiment-01
laplacian-blur-benchmark data/new-labels.csv --policy outputs/experiment-01/policy.json --output outputs/experiment-02
```

Thresholds are selected per domain using calibration samples only. Held-out test
reports include false rejections, missed retakes, confusion counts, and an error
list. Reports preserve policy, preprocessing, dataset fingerprints, and runtime
versions, and refuse to overwrite previous runs. Capture-group and duplicate-image
checks help catch calibration/test overlap.

See [the benchmarking guide](docs/BENCHMARKING.md) for the CSV format, objective,
limitations, and a runnable synthetic document/product dataset example. Human
labels and real representative data are needed to assess accuracy.

## Validation and packaging

```bash
python -m ruff check .
python -m pytest -q
python -m build
node --test tests/web/batch-utils.test.mjs
```

CI is configured to run on Ubuntu and Windows with Python 3.10, 3.12, and 3.13.
It lints, runs regression tests, builds the source distribution and wheel, and
checks the installed CLI/API/assets outside the checkout. GitHub branch protection,
required reviews, and publishing remain maintainer configuration tasks.

See the contribution guide for installed-wheel verification and release steps.

## Docker

```bash
docker build -t laplacian-blur-detector .
docker run --rm -p 8000:8000 laplacian-blur-detector
```

The image installs the server extra and includes the browser tool and upload
limits. Containerization does not add authentication or per-client rate limiting.

## License

Original project code is [MIT licensed](LICENSE). Dependencies keep their own
licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
