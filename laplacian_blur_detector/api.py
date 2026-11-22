"""Bounded HTTP image analysis with single-image and batch interfaces."""

from contextlib import contextmanager
from io import BytesIO
import json
from pathlib import Path
from threading import BoundedSemaphore
from time import perf_counter

import cv2
from PIL import Image
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from . import __version__
from .blur_detector import detect_blur
from .config import (
    DEFAULT_BLUR_THRESHOLD, MAX_UPLOAD_BYTES, MAX_IMAGE_PIXELS, MAX_BATCH_FILES,
    MAX_BATCH_BYTES, MULTIPART_OVERHEAD_BYTES, MAX_CONCURRENT_ANALYSES,
    DEFAULT_LOCAL_GRID_SIZE, MAX_LOCAL_GRID_SIZE, MIN_LOCAL_CELL_SIZE,
    MAX_DIAGNOSTIC_POLICY_BYTES,
)
from .diagnostics import DiagnosticPolicy, diagnose_image_quality
from .evaluation import finite_nonnegative
from .image_utils import decode_image_bytes
from .request_limits import UploadBodyLimitMiddleware
from .sharpness import analyze_local_sharpness
from .upload_validation import UploadValidationError, validate_header

PACKAGE_ROOT = Path(__file__).resolve().parent
WEB_DIRECTORY = PACKAGE_ROOT / "web"
if not WEB_DIRECTORY.is_dir():
    WEB_DIRECTORY = PACKAGE_ROOT.parent / "web"

app = FastAPI(title="Laplacian Blur Detector", version=__version__)
app.mount("/static", StaticFiles(directory=WEB_DIRECTORY), name="static")
app.add_middleware(UploadBodyLimitMiddleware, limits={
    "/api/blur/check": MAX_UPLOAD_BYTES + MULTIPART_OVERHEAD_BYTES,
    "/api/blur/batch": MAX_BATCH_BYTES + MULTIPART_OVERHEAD_BYTES,
    "/api/sharpness/local": MAX_UPLOAD_BYTES + MULTIPART_OVERHEAD_BYTES,
    "/api/quality/diagnose": MAX_UPLOAD_BYTES + MULTIPART_OVERHEAD_BYTES,
})
_analysis_slots = BoundedSemaphore(MAX_CONCURRENT_ANALYSES)


@app.exception_handler(UploadValidationError)
async def upload_error(request: Request, error: UploadValidationError) -> JSONResponse:
    return JSONResponse(
        {"detail": str(error), "error_code": error.code},
        status_code=error.status_code,
        headers={"Retry-After": "1"} if error.status_code == 503 else None,
    )


@app.get("/", include_in_schema=False)
def web_demo() -> FileResponse:
    return FileResponse(WEB_DIRECTORY / "index.html")


@app.get("/healthz")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/config")
def public_config() -> dict:
    """Expose the same limits and defaults used by the server to browser clients."""
    return {
        "default_threshold": DEFAULT_BLUR_THRESHOLD,
        "max_upload_bytes": MAX_UPLOAD_BYTES,
        "max_image_pixels": MAX_IMAGE_PIXELS,
        "max_batch_files": MAX_BATCH_FILES,
        "max_batch_bytes": MAX_BATCH_BYTES,
        "supported_extensions": [".jpg", ".jpeg", ".png"],
        "local_sharpness": {
            "default_grid_size": DEFAULT_LOCAL_GRID_SIZE,
            "max_grid_size": MAX_LOCAL_GRID_SIZE,
            "max_cells": MAX_LOCAL_GRID_SIZE**2,
            "min_cell_size": MIN_LOCAL_CELL_SIZE,
        },
    }


def _resolve_threshold(threshold: float) -> float:
    try:
        return finite_nonnegative(threshold)
    except ValueError as error:
        raise UploadValidationError("Threshold must be a finite non-negative number.", "INVALID_THRESHOLD") from error


@contextmanager
def _validated_analysis_image(data: bytes, filename: str):
    """Share header/decode limits and hold the same slot through all analysis."""
    if not _analysis_slots.acquire(blocking=False):
        raise UploadValidationError("The service is busy. Please retry shortly.", "SERVICE_BUSY", 503)
    try:
        validate_header(data, filename, MAX_IMAGE_PIXELS)
        try:
            image = decode_image_bytes(data, filename)
            height, width = image.shape[:2]
            if width * height > MAX_IMAGE_PIXELS:
                raise UploadValidationError("Image dimensions are too large. Resize it before uploading.", "IMAGE_TOO_LARGE", 413)
            yield image
        except UploadValidationError:
            raise
        except (ValueError, cv2.error) as error:
            raise UploadValidationError("Could not analyze uploaded image. Use a valid JPG, JPEG, or PNG.") from error
    finally:
        _analysis_slots.release()


def _analyze_bytes(data: bytes, filename: str, threshold: float) -> dict:
    started = perf_counter()
    with _validated_analysis_image(data, filename) as image:
        height, width = image.shape[:2]
        result = detect_blur(image, threshold)
        return {
            "success": True,
            "filename": filename,
            "width": width,
            "height": height,
            "file_size": len(data),
            **result,
            "processing_ms": round((perf_counter() - started) * 1000, 2),
            "message": (
                "Image is too blurry. Please retake the photo."
                if result["is_blurry"] else "Image passes the sharpness threshold."
            ),
        }


async def _read_upload(image: UploadFile) -> bytes:
    data = await image.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise UploadValidationError(
            f"Image exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MiB upload limit.",
            "FILE_TOO_LARGE", 413,
        )
    return data


async def _analyze_upload(image: UploadFile, threshold: float) -> dict:
    data = await _read_upload(image)
    return await run_in_threadpool(_analyze_bytes, data, image.filename or "uploaded-image.png", threshold)


def _display_oriented(image, data: bytes):
    """Match browser EXIF orientation for heatmap coordinates, including mirrors."""
    try:
        with Image.open(BytesIO(data)) as header:
            orientation = header.getexif().get(274, 1)
    except (OSError, SyntaxError, ValueError) as error:
        raise UploadValidationError("Could not read image orientation metadata.") from error
    if orientation == 2:
        return cv2.flip(image, 1)
    if orientation == 3:
        return cv2.rotate(image, cv2.ROTATE_180)
    if orientation == 4:
        return cv2.flip(image, 0)
    if orientation == 5:
        return cv2.transpose(image)
    if orientation == 6:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    if orientation == 7:
        return cv2.flip(cv2.transpose(image), -1)
    if orientation == 8:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return image


def _analyze_local_bytes(data: bytes, filename: str, metric: str, rows: int, columns: int, texture_cutoff: float) -> dict:
    started = perf_counter()
    with _validated_analysis_image(data, filename) as image:
        image = _display_oriented(image, data)
        height, width = image.shape[:2]
        if height // rows < MIN_LOCAL_CELL_SIZE or width // columns < MIN_LOCAL_CELL_SIZE:
            raise UploadValidationError(
                f"Each cell must be at least {MIN_LOCAL_CELL_SIZE} x {MIN_LOCAL_CELL_SIZE} pixels. Choose a smaller grid.",
                "GRID_TOO_FINE",
            )
        cells = analyze_local_sharpness(image, (rows, columns), metric, min_texture_std=texture_cutoff)
        return {
            "success": True, "filename": filename, "width": width, "height": height,
            "file_size": len(data), "metric": metric,
            "grid_rows": rows, "grid_columns": columns, "min_texture_std": texture_cutoff,
            "coordinate_space": "exif_oriented_pixels", "cells": cells,
            "processing_ms": round((perf_counter() - started) * 1000, 2),
        }


@app.post("/api/sharpness/local")
async def local_sharpness(
    image: UploadFile = File(...),
    metric: str = Form("laplacian"),
    grid_rows: int = Form(DEFAULT_LOCAL_GRID_SIZE),
    grid_columns: int = Form(DEFAULT_LOCAL_GRID_SIZE),
    min_texture_std: float = Form(5.0),
) -> dict:
    """Return local measurements, not blur labels or cross-image normalized scores."""
    try:
        if metric not in ("laplacian", "tenengrad"):
            raise UploadValidationError("Metric must be 'laplacian' or 'tenengrad'.", "INVALID_METRIC")
        if not (1 <= grid_rows <= MAX_LOCAL_GRID_SIZE and 1 <= grid_columns <= MAX_LOCAL_GRID_SIZE):
            raise UploadValidationError(f"Grid rows and columns must be between 1 and {MAX_LOCAL_GRID_SIZE}.", "INVALID_GRID")
        try:
            cutoff = finite_nonnegative(min_texture_std)
        except ValueError as error:
            raise UploadValidationError("Texture cutoff must be finite and non-negative.", "INVALID_TEXTURE_CUTOFF") from error
        data = await _read_upload(image)
        return await run_in_threadpool(
            _analyze_local_bytes, data, image.filename or "uploaded-image.png",
            metric, grid_rows, grid_columns, cutoff,
        )
    finally:
        await image.close()


def _parse_diagnostic_policy(value: str) -> DiagnosticPolicy:
    def unique_fields(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise ValueError("Duplicate policy fields are not allowed.")
            result[key] = item
        return result

    def finite_json(token):
        raise ValueError("Non-finite JSON values are not allowed.")

    try:
        if len(value.encode("utf-8")) > MAX_DIAGNOSTIC_POLICY_BYTES:
            raise UploadValidationError("Diagnostic policy exceeds the 8 KiB limit.", "DIAGNOSTIC_POLICY_TOO_LARGE", 413)
        parsed = json.loads(value, object_pairs_hook=unique_fields, parse_constant=finite_json)
        return DiagnosticPolicy.from_mapping(parsed)
    except UploadValidationError:
        raise
    except (ValueError, TypeError, RecursionError, UnicodeError) as error:
        # JSON-escaped surrogate keys must not turn a policy error into HTTP 500.
        detail = str(error).encode("utf-8", "backslashreplace").decode("utf-8")
        raise UploadValidationError("Invalid diagnostic policy: " + detail, "INVALID_DIAGNOSTIC_POLICY") from error


def _analyze_quality_bytes(data: bytes, filename: str, policy: DiagnosticPolicy) -> dict:
    started = perf_counter()
    with _validated_analysis_image(data, filename) as image:
        image = _display_oriented(image, data)
        height, width = image.shape[:2]
        try:
            report = diagnose_image_quality(image, policy)
        except ValueError as error:
            raise UploadValidationError(str(error), "INVALID_DIAGNOSTIC_INPUT") from error
        return {
            "success": True, "filename": filename, "width": width, "height": height,
            "file_size": len(data), "coordinate_space": "exif_oriented_pixels",
            "processing_ms": round((perf_counter() - started) * 1000, 2), **report,
        }


@app.post("/api/quality/diagnose")
async def quality_diagnostics(image: UploadFile = File(...), policy: str = Form("{}")) -> dict:
    """Independent advisory diagnostics with bounded input and opt-in policy."""
    try:
        resolved = _parse_diagnostic_policy(policy)
        data = await _read_upload(image)
        return await run_in_threadpool(_analyze_quality_bytes, data, image.filename or "uploaded-image.png", resolved)
    finally:
        await image.close()


@app.post("/api/blur/check")
async def check_blur(
    image: UploadFile = File(...),
    threshold: float = Form(DEFAULT_BLUR_THRESHOLD),
) -> dict:
    """Check one JPG/JPEG/PNG, with bounded file size and decoded dimensions."""
    try:
        return await _analyze_upload(image, _resolve_threshold(threshold))
    finally:
        await image.close()


@app.post("/api/blur/batch")
async def check_batch(
    images: list[UploadFile] = File(...),
    threshold: float = Form(DEFAULT_BLUR_THRESHOLD),
) -> dict:
    """Analyze in input order; individual invalid files do not abort valid files."""
    try:
        resolved = _resolve_threshold(threshold)
        if len(images) > MAX_BATCH_FILES:
            raise UploadValidationError(f"Select at most {MAX_BATCH_FILES} images per batch.", "BATCH_LIMIT")
        if sum(image.size or 0 for image in images) > MAX_BATCH_BYTES:
            raise UploadValidationError("Batch exceeds the total upload limit. Send fewer or smaller images.", "BATCH_TOO_LARGE", 413)
        results = []
        for image in images:
            try:
                results.append(await _analyze_upload(image, resolved))
            except UploadValidationError as error:
                results.append({
                    "success": False, "filename": image.filename or "uploaded-image.png",
                    "status_code": error.status_code, "error_code": error.code, "message": str(error),
                })
            finally:
                await image.close()
        processed = sum(result["success"] for result in results)
        blurry = sum(result.get("is_blurry", False) for result in results)
        return {
            "success": processed == len(images), "total": len(images),
            "processed": processed, "failed": len(images) - processed,
            "clear": processed - blurry, "blurry": blurry,
            "threshold": resolved, "results": results,
        }
    finally:
        for image in images:
            await image.close()
