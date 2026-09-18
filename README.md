# Laplacian Blur Detector

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-009688?logo=fastapi&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-Laplacian%20Variance-5C3EE8?logo=opencv&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-72D3B2)

A lightweight standalone image-sharpness service built with OpenCV and FastAPI. Upload a photo, receive a Laplacian variance score, and classify it as **CLEAR** or **BLURRY**. It is designed to run independently today and integrate into a future iRent upload pipeline without coupling to iRent code.

## Overview

This repository provides three useful interfaces:

- An interactive browser demo at `/`.
- A REST API for backend integration.
- Reusable Python functions, a CLI, and dataset-evaluation tool.

No images are stored, no database is used, and no machine-learning model is involved.

## Features

- Laplacian Variance Blur Detection
- Interactive Web Demo
- REST API
- Adjustable Blur Threshold
- Batch Dataset Evaluation
- CSV Export
- CLI
- Automated Tests
- Docker Support

## How It Works

```text
Image
  ↓
Grayscale
  ↓
Laplacian Operator
  ↓
Variance
  ↓
Blur Score
  ↓
Threshold Comparison
  ↓
CLEAR / BLURRY
```

The detector computes `cv2.Laplacian(gray, cv2.CV_64F).var()`. Higher variance generally means more edge information and a sharper image. Lower variance generally means fewer or smoother edges and a blurrier image. This is a traditional computer-vision sharpness metric, not an AI or learned model.

## Architecture

```text
                 Web UI
                    ↓
                  API
                    ↓
             Blur Detector Core
                    ↑
               CLI / Dataset Tool
```

`src/blur_detector.py` has no dependency on FastAPI, HTML, iRent, or a database. Use `calculate_blur_score(image)` for the metric, or `detect_blur(image, threshold)` for the classification.

## Installation

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Quick Start

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

When running, open:

- Web demo: <http://localhost:8000>
- Interactive API documentation: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/healthz>

## Web Demo

The browser demo accepts JPG, JPEG, and PNG files. It previews a selected image locally, lets you choose a threshold, and calls the API only when you choose **Analyze image**. It displays filename, resolution, file size, score, threshold, a prominent CLEAR/BLURRY result, and a score bar that remains valid for unusually high scores.

## REST API

### `GET /healthz`

```json
{"status": "ok"}
```

### `POST /api/blur/check`

Accepts `multipart/form-data` fields `image` (JPG/JPEG/PNG) and optional `threshold`.

```bash
curl -X POST http://localhost:8000/api/blur/check \
  -F "image=@path/to/car.jpg" \
  -F "threshold=120"
```

Example response:

```json
{
  "success": true,
  "filename": "car.jpg",
  "width": 1280,
  "height": 720,
  "file_size": 862208,
  "blur_score": 184.72,
  "threshold": 100.0,
  "is_blurry": false,
  "message": "Image quality is acceptable."
}
```

Swagger UI is available at <http://localhost:8000/docs>.

## CLI

```bash
python scripts/test_image.py path/to/image.jpg
python scripts/test_image.py path/to/image.jpg --threshold 120
```

The output includes image name, resolution, score, threshold, and classification.

## Dataset Evaluation

```bash
python scripts/evaluate_dataset.py ./samples
```

This writes `outputs/blur_scores.csv` containing `filename`, `width`, `height`, `file_size`, `blur_score`, `threshold`, and `is_blurry`. Unreadable files are reported and skipped; source images are never modified.

## Docker

```bash
docker build -t laplacian-blur-detector .
docker run --rm -p 8000:8000 laplacian-blur-detector
```

Then visit <http://localhost:8000>, <http://localhost:8000/docs>, or <http://localhost:8000/healthz>.

## Threshold Calibration

`DEFAULT_BLUR_THRESHOLD = 100.0` is a development default, not a universal quality rule. Calibrate a production threshold using representative photos for the actual camera, image resolution, compression, lighting, vehicle photo distance, and real iRent dataset. Inspect the generated CSV distribution before choosing a rejection threshold.

## Testing

```bash
python -m pytest -q
```

Tests generate synthetic sharp and blurred images locally. They cover the core calculation, the threshold boundary, invalid input, `/`, `/healthz`, and `POST /api/blur/check` including a custom threshold.

## Future iRent Integration

Keep this service behind the iRent backend rather than calling it directly from an iRent frontend:

```text
iRent Frontend
      ↓
iRent Backend
      ↓
Blur Detection Service
      ↓
CLEAR?
   ├─ No → Request Retake
   └─ Yes → Continue iRent Upload Pipeline
```

At upload time, the iRent backend should correct EXIF orientation first, then call `POST /api/blur/check` before persistent storage. A blurry result should ask the user to retake the photo; a clear one can proceed. The core can also be imported directly, but the API boundary keeps future deployment and replacement independent.

## Limitations

Laplacian variance measures edge detail, not every kind of image quality. A dark, low-contrast, highly compressed, naturally low-detail, or motion-blurred scene can need separate product rules. Use it as a fast quality gate together with calibration on real-world photos.
