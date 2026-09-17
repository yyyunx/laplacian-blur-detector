"""HTTP interface for the standalone blur detector."""

from fastapi import FastAPI, File, HTTPException, UploadFile

from src.blur_detector import detect_blur
from src.config import DEFAULT_BLUR_THRESHOLD
from src.image_utils import decode_image_bytes

app = FastAPI(title="Laplacian Blur Detector", version="0.1.0")


@app.get("/healthz")
def health_check() -> dict[str, str]:
    """Return a simple service health response."""
    return {"status": "ok"}


@app.post("/api/blur/check")
async def check_blur(image: UploadFile = File(...)) -> dict[str, bool | float | str]:
    """Check an uploaded JPG, JPEG, or PNG image for blur."""
    try:
        decoded_image = decode_image_bytes(await image.read(), image.filename)
        result = detect_blur(decoded_image, DEFAULT_BLUR_THRESHOLD)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    is_blurry = result["is_blurry"]
    return {
        "success": True,
        **result,
        "message": (
            "Image is too blurry. Please retake the photo."
            if is_blurry
            else "Image quality is acceptable."
        ),
    }
