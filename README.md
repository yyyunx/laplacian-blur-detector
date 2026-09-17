# Laplacian Blur Detector

A standalone Laplacian Blur Detection Service for checking vehicle-upload photos before they enter the future iRent flow. This repository is intentionally independent: it does not modify or import any iRent code.

## Purpose

The service measures whether an uploaded photo is likely too blurry to be useful. It provides a reusable Python core, a small command-line tool for calibration, and a FastAPI endpoint for later integration.

## Algorithm

```text
Image
  ↓
Grayscale
  ↓
Laplacian Edge Detection
  ↓
Variance
  ↓
Blur Score
  ↓
Threshold Comparison
  ↓
Clear / Blurry
```

The calculation is:

```python
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
score = cv2.Laplacian(gray, cv2.CV_64F).var()
```

Laplacian is sensitive to edges and other high-frequency detail. Clear photos usually retain more distinct edges, yielding higher variance; blur smooths those edges, generally yielding lower variance. An image is blurry only when `blur_score < threshold`; an equal score is clear.

## Installation

```bash
python -m venv .venv
```

Windows activation:

```powershell
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## CLI usage

Score one JPG, JPEG, or PNG image:

```bash
python scripts/test_image.py path/to/image.jpg
python scripts/test_image.py path/to/image.jpg --threshold 120
```

Evaluate a directory recursively and write `outputs/blur_scores.csv`:

```bash
python scripts/evaluate_dataset.py ./samples
python scripts/evaluate_dataset.py ./samples --threshold 120
```

The CSV includes each relative filename, image width and height, score, threshold, and blurry classification. Unreadable supported files are skipped and reported; source images are never altered.

## API usage

Start the service from the repository root:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/healthz
```

Check an image:

```bash
curl -X POST http://127.0.0.1:8000/api/blur/check -F "image=@path/to/image.jpg"
```

For a blurry image, the response includes `"message": "Image is too blurry. Please retake the photo."`; otherwise it reports that quality is acceptable. Invalid, empty, non-image, or unsupported uploads return HTTP 400 with a clear error.

## Threshold calibration

`DEFAULT_BLUR_THRESHOLD` is **100.0**. This is only a starting threshold; it is not suitable for every camera, resolution, or scene. Calibrate it later using real iRent photos and the generated score distribution before treating it as a production decision boundary.

## Future iRent integration

Keep this project as the photo-quality boundary. A future iRent upload flow should correct EXIF orientation before calling the detector, then reject a blurry image before storage:

```text
iRent photo upload
        ↓
EXIF orientation correction
        ↓
Laplacian blur check
        ↓
Too blurry?
   ├─ Yes → reject + ask user to retake
   └─ No  → continue upload
```

iRent can either import the independent core:

```python
from src.blur_detector import detect_blur
```

or invoke `POST /api/blur/check`. In either case, integrate at the server-side photo-upload validation layer, before persistent storage; do not put this decision in a frontend-only check.

## Tests

```bash
pytest
```

Tests generate synthetic sharp and blurred images locally, so no test-image download is required.
