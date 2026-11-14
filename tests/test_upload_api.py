"""Batch behavior, bounded uploads, and header checks before pixel decoding."""

from io import BytesIO
from threading import BoundedSemaphore

import cv2
from fastapi import FastAPI, File, UploadFile
from fastapi.testclient import TestClient
import numpy as np
from PIL import Image
import pytest

from laplacian_blur_detector import api
from laplacian_blur_detector.request_limits import UploadBodyLimitMiddleware


def png(value=0, size=16):
    ok, encoded = cv2.imencode(".png", np.full((size, size, 3), value, dtype=np.uint8))
    assert ok
    return encoded.tobytes()


def test_batch_keeps_input_order_and_reports_invalid_files_individually():
    with TestClient(api.app) as client:
        response = client.post("/api/blur/batch", data={"threshold": "0"}, files=[
            ("images", ("first.png", png(), "image/png")),
            ("images", ("bad.txt", b"invalid", "text/plain")),
            ("images", ("first.png", png(40), "image/png")),
        ])
    assert response.status_code == 200
    result = response.json()
    assert result["total"] == 3 and result["processed"] == 2 and result["failed"] == 1
    assert result["clear"] == 2 and result["blurry"] == 0
    assert result["success"] is False
    assert [row["filename"] for row in result["results"]] == ["first.png", "bad.txt", "first.png"]
    assert result["results"][1]["error_code"] == "UNSUPPORTED_FORMAT"
    assert result["results"][0]["threshold"] == 0


def test_pixel_limit_is_checked_before_opencv_decode(monkeypatch):
    image = png(size=4)
    monkeypatch.setattr(api, "MAX_IMAGE_PIXELS", 15)

    def forbidden(*args, **kwargs):
        raise AssertionError("Oversized image must not be decoded")

    monkeypatch.setattr(cv2, "imdecode", forbidden)
    with TestClient(api.app) as client:
        response = client.post("/api/blur/check", files={"image": ("large.png", image, "image/png")})
    assert response.status_code == 413
    assert response.json()["error_code"] == "IMAGE_TOO_LARGE"


def test_file_limit_returns_actionable_413(monkeypatch):
    monkeypatch.setattr(api, "MAX_UPLOAD_BYTES", 10)
    with TestClient(api.app) as client:
        response = client.post("/api/blur/check", files={"image": ("large.png", png(), "image/png")})
    assert response.status_code == 413
    assert response.json()["error_code"] == "FILE_TOO_LARGE"


@pytest.mark.parametrize("route,field", [("/api/blur/check", "image"), ("/api/blur/batch", "images")])
def test_invalid_threshold_does_not_start_analysis(monkeypatch, route, field):
    def forbidden(*args, **kwargs):
        raise AssertionError("Invalid threshold must not start image processing")

    monkeypatch.setattr(api, "_analyze_bytes", forbidden)
    with TestClient(api.app) as client:
        response = client.post(route, data={"threshold": "nan"}, files={field: ("image.png", png(), "image/png")})
    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_THRESHOLD"


@pytest.mark.parametrize("count_limit,byte_limit,code", [(1, 100000, "BATCH_LIMIT"), (20, 1, "BATCH_TOO_LARGE")])
def test_batch_limits_reject_whole_request(monkeypatch, count_limit, byte_limit, code):
    monkeypatch.setattr(api, "MAX_BATCH_FILES", count_limit)
    monkeypatch.setattr(api, "MAX_BATCH_BYTES", byte_limit)
    with TestClient(api.app) as client:
        response = client.post("/api/blur/batch", files=[
            ("images", ("one.png", png(), "image/png")),
            ("images", ("two.png", png(40), "image/png")),
        ])
    assert response.status_code in (400, 413)
    assert response.json()["error_code"] == code


def test_busy_service_replies_with_retry_hint_and_recovers(monkeypatch):
    slots = BoundedSemaphore(1)
    monkeypatch.setattr(api, "_analysis_slots", slots)
    slots.acquire()
    with TestClient(api.app) as client:
        response = client.post("/api/blur/check", files={"image": ("image.png", png(), "image/png")})
        assert response.status_code == 503
        assert response.headers["Retry-After"] == "1"
        assert response.json()["error_code"] == "SERVICE_BUSY"
        slots.release()
        assert client.post("/api/blur/check", files={"image": ("image.png", png(), "image/png")} ).status_code == 200


def test_decoder_failure_does_not_leak_analysis_slot(monkeypatch):
    monkeypatch.setattr(api, "_analysis_slots", BoundedSemaphore(1))
    with TestClient(api.app) as client:
        assert client.post("/api/blur/check", files={"image": ("broken.png", b"bad", "image/png")} ).status_code == 400
        assert client.post("/api/blur/check", files={"image": ("ok.png", png(), "image/png")} ).status_code == 200


def test_gif_renamed_to_png_is_rejected():
    stream = BytesIO()
    Image.new("RGB", (10, 10)).save(stream, format="GIF")
    with TestClient(api.app) as client:
        response = client.post("/api/blur/check", files={"image": ("renamed.png", stream.getvalue(), "image/png")})
    assert response.status_code == 400


def test_animated_png_is_not_silently_scored_as_a_still_image():
    stream = BytesIO()
    Image.new("RGB", (10, 10)).save(stream, format="PNG", save_all=True, append_images=[Image.new("RGB", (10, 10), "red")])
    with TestClient(api.app) as client:
        response = client.post("/api/blur/check", files={"image": ("animated.png", stream.getvalue(), "image/png")})
    assert response.status_code == 400
    assert response.json()["error_code"] == "ANIMATED_IMAGE"


@pytest.mark.parametrize("chunked", [False, True])
def test_multipart_request_limit_catches_declared_and_streaming_bodies(chunked):
    app = FastAPI()
    app.add_middleware(UploadBodyLimitMiddleware, limits={"/upload": 150})

    @app.post("/upload")
    async def upload(image: UploadFile = File(...)):
        pytest.fail("Oversized body must not reach the endpoint")

    body = b'--boundary\r\nContent-Disposition: form-data; name="image"; filename="large.png"\r\nContent-Type: image/png\r\n\r\n' + b"x" * 200 + b"\r\n--boundary--\r\n"
    headers = {"Content-Type": "multipart/form-data; boundary=boundary"}
    content = (body[index:index + 20] for index in range(0, len(body), 20)) if chunked else body
    with TestClient(app) as client:
        response = client.post("/upload", content=content, headers=headers)
    assert response.status_code == 413
    assert response.json()["error_code"] == "REQUEST_TOO_LARGE"


def test_public_config_matches_enforced_defaults():
    with TestClient(api.app) as client:
        result = client.get("/api/config").json()
    assert result["max_upload_bytes"] == api.MAX_UPLOAD_BYTES
    assert result["max_image_pixels"] == api.MAX_IMAGE_PIXELS
    assert result["max_batch_files"] == api.MAX_BATCH_FILES
