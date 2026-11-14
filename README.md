# Laplacian Blur Detector

![Tests](https://github.com/yyyunx/laplacian-blur-detector/actions/workflows/tests.yml/badge.svg)

A reusable image-sharpness library, command-line tool, and optional HTTP service.
The project is growing toward an open-source image quality toolkit and a shared
review workspace. Vehicle photos are one use case alongside document capture,
product photography, and other image upload workflows.

**Current status: early-stage, stateless toolkit.** It computes Laplacian variance;
it is not a learned model or a complete image quality assessment. Team accounts,
shared datasets, annotation, and review queues are planned, not implemented.

## Choose how to use it

| Interface | Useful for |
| --- | --- |
| Python library | Integrating measurements into your own application |
| Single-image CLI | Checking an image locally |
| Dataset CLI with CSV | Inspecting score distributions across a folder |
| Labeled benchmark CLI | Calibrating domain policies and reporting held-out mistakes |
| Optional API and browser demo | Trying uploads and connecting another backend |

No images are persisted by the API. The browser previews selected images locally
and uploads them only when analysis is requested. The dataset CLI writes local CSV.

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

## Labeled evaluation and calibration

Label a dataset with `filename,label,split,group,domain` (optional `reason`), then run:

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

## Browser demo and API

Install the `server` extra, then run:

```bash
laplacian-blur-serve
```

Open the demo at <http://127.0.0.1:8000>, interactive API documentation at
<http://127.0.0.1:8000/docs>, or health check at <http://127.0.0.1:8000/healthz>.
Use `--host` and `--port` to choose the listener. The existing checkout command
`uvicorn api.main:app --host 127.0.0.1 --port 8000` also works.

The demo supports JPG/JPEG/PNG preview, an adjustable threshold, image metadata,
a CLEAR/BLURRY result, a score bar, and the raw API response.

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
  "message": "Image quality is acceptable."
}
```

The message currently reflects only the blur threshold. Empty, undecodable, or
unsupported uploads and invalid non-negative finite thresholds return an error.
`GET /healthz` returns `{"status": "ok"}`.

The HTTP service has no authentication, resource quotas, or upload-size/pixel
limits yet. Review [SECURITY.md](SECURITY.md) before deploying it beyond a trusted
environment. The included demo is not a multi-user platform.

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

- [Roadmap](docs/ROADMAP.md): open-source foundation, reproducible evaluation,
  shared review workspace, reliable team operation, broader quality metrics.
- [Architecture](docs/ARCHITECTURE.md): public interfaces, extension boundaries,
  and the proposed collaboration data model.
- [Changelog](CHANGELOG.md): behavior and compatibility changes.
- [Security policy](SECURITY.md): reporting and deployment boundaries.

Labeled evaluation and versioned quality policies are available locally. The next
team platform milestone adds projects, permissions,
shared labeling, review decisions, and history that survives policy changes.

## Validation and packaging

```bash
python -m ruff check .
python -m pytest -q
python -m build
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

The image installs the server extra and includes the browser demo. Containerization
does not add the missing authentication or resource limits.

## License

Original project code is [MIT licensed](LICENSE). Dependencies keep their own
licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
