"""Header validation for HTTP uploads before OpenCV allocates decoded pixels."""

from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from .image_utils import SUPPORTED_IMAGE_EXTENSIONS


class UploadValidationError(ValueError):
    def __init__(self, message: str, code: str = "INVALID_IMAGE", status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def validate_header(data: bytes, filename: str, max_pixels: int) -> None:
    """Accept supported single-frame files and inspect dimensions without loading pixels."""
    if Path(filename).suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise UploadValidationError("Unsupported image format. Use JPG, JPEG, or PNG.", "UNSUPPORTED_FORMAT")
    if not data:
        raise UploadValidationError("Image upload is empty.", "EMPTY_IMAGE")
    try:
        with Image.open(BytesIO(data), formats=["JPEG", "PNG"]) as header:
            width, height = header.size
            if width * height > max_pixels:
                raise UploadValidationError(
                    f"Image exceeds the {max_pixels:,}-pixel limit. Resize it before uploading.",
                    "IMAGE_TOO_LARGE", 413,
                )
            if getattr(header, "is_animated", False):
                raise UploadValidationError("Animated images are not supported. Upload a still image.", "ANIMATED_IMAGE")
    except Image.DecompressionBombError as error:
        raise UploadValidationError("Image dimensions are too large. Resize it before uploading.", "IMAGE_TOO_LARGE", 413) from error
    except (UnidentifiedImageError, OSError, SyntaxError) as error:
        raise UploadValidationError("Could not decode uploaded image. Use a valid JPG, JPEG, or PNG.") from error
