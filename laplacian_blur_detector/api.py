"""Bounded HTTP image analysis with single-image and batch interfaces."""

from pathlib import Path
from threading import BoundedSemaphore
from time import perf_counter

import cv2
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from . import __version__
from .blur_detector import detect_blur
from .config import (
    DEFAULT_BLUR_THRESHOLD, MAX_UPLOAD_BYTES, MAX_IMAGE_PIXELS, MAX_BATCH_FILES,
    MAX_BATCH_BYTES, MULTIPART_OVERHEAD_BYTES, MAX_CONCURRENT_ANALYSES,
)
from .evaluation import finite_nonnegative
from .image_utils import decode_image_bytes
from .request_limits import UploadBodyLimitMiddleware
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
    }


def _resolve_threshold(threshold: float) -> float:
    try:
        return finite_nonnegative(threshold)
    except ValueError as error:
        raise UploadValidationError("Threshold must be a finite non-negative number.", "INVALID_THRESHOLD") from error


def _analyze_bytes(data: bytes, filename: str, threshold: float) -> dict:
    if not _analysis_slots.acquire(blocking=False):
        raise UploadValidationError("The service is busy. Please retry shortly.", "SERVICE_BUSY", 503)
    try:
        started = perf_counter()
        validate_header(data, filename, MAX_IMAGE_PIXELS)
        try:
            image = decode_image_bytes(data, filename)
            height, width = image.shape[:2]
            if width * height > MAX_IMAGE_PIXELS:
                raise UploadValidationError("Image dimensions are too large. Resize it before uploading.", "IMAGE_TOO_LARGE", 413)
            result = detect_blur(image, threshold)
        except UploadValidationError:
            raise
        except (ValueError, cv2.error) as error:
            raise UploadValidationError("Could not analyze uploaded image. Use a valid JPG, JPEG, or PNG.") from error
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
    finally:
        _analysis_slots.release()


async def _analyze_upload(image: UploadFile, threshold: float) -> dict:
    data = await image.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise UploadValidationError(
            f"Image exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MiB upload limit.",
            "FILE_TOO_LARGE", 413,
        )
    return await run_in_threadpool(_analyze_bytes, data, image.filename or "uploaded-image.png", threshold)


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
