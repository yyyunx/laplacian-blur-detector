"""HTTP interface and static demo for the standalone blur detector."""

from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.blur_detector import detect_blur
from src.config import DEFAULT_BLUR_THRESHOLD
from src.image_utils import decode_image_bytes

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_DIRECTORY = PROJECT_ROOT / "web"

app = FastAPI(title="Laplacian Blur Detector", version="0.2.0")
app.mount("/static", StaticFiles(directory=WEB_DIRECTORY), name="static")


@app.get("/", include_in_schema=False)
def web_demo() -> FileResponse:
    """Serve the standalone browser demo."""
    return FileResponse(WEB_DIRECTORY / "index.html")


@app.get("/healthz")
def health_check() -> dict[str, str]:
    """Return a simple service health response."""
    return {"status": "ok"}


@app.post("/api/blur/check")
async def check_blur(
    image: UploadFile = File(...),
    threshold: float = Form(DEFAULT_BLUR_THRESHOLD),
) -> dict[str, bool | float | int | str]:
    """Check an uploaded JPG, JPEG, or PNG image for blur."""
    try:
        image_bytes = await image.read()
        decoded_image = decode_image_bytes(image_bytes, image.filename)
        result = detect_blur(decoded_image, threshold)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    is_blurry = result["is_blurry"]
    height, width = decoded_image.shape[:2]
    return {
        "success": True,
        "filename": image.filename or "uploaded-image",
        "width": width,
        "height": height,
        "file_size": len(image_bytes),
        **result,
        "message": (
            "Image is too blurry. Please retake the photo."
            if is_blurry
            else "Image quality is acceptable."
        ),
    }
