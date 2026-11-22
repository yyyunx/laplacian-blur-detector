"""Quality route contract, policy safety, shared limits and oriented measurements."""

from io import BytesIO
import json
from threading import BoundedSemaphore

import cv2
import numpy as np
from fastapi.testclient import TestClient
from PIL import Image, ImageOps
import pytest

from laplacian_blur_detector import DiagnosticPolicy, diagnose_image_quality
from laplacian_blur_detector import api

ROUTE = "/api/quality/diagnose"


def encoded(image=None):
    if image is None:
        image = np.tile(np.arange(128, dtype=np.uint8), (96, 1))
    ok, result = cv2.imencode(".png", image)
    assert ok
    return result.tobytes()


def post(client, policy="{}", content=None, filename="sample.png"):
    return client.post(ROUTE, data={"policy": policy}, files={"image": (filename, encoded() if content is None else content, "image/png")})


def test_api_matches_core_and_keeps_the_explicit_policy():
    image = np.tile(np.arange(128, dtype=np.uint8), (96, 1))
    options = {"min_mean_brightness": 0.5, "max_dark_ratio": 0.1, "min_width": 640}
    expected = diagnose_image_quality(image, DiagnosticPolicy.from_mapping(options))
    with TestClient(api.app) as client:
        response = post(client, json.dumps(options), encoded(image))
    assert response.status_code == 200
    payload = response.json()
    assert payload["measurements"] == expected["measurements"]
    assert payload["checks"] == expected["checks"]
    assert payload["policy"] == expected["policy"]
    assert payload["coordinate_space"] == "exif_oriented_pixels"
    assert (payload["width"], payload["height"]) == (128, 96)
    assert "accepted" not in payload and "is_blurry" not in payload


@pytest.mark.parametrize("policy", ['{"unknown":1}', '{"max_dark_ratio":NaN}', '{"min_width":true}',
                                     '{"min_width":1,"min_width":2}', '[]', '{',
                                     '{"\\ud800":1}', '{"min_tenengrad_score":1e400}', '[' * 1100 + ']' * 1100])
def test_invalid_policy_rejects_before_image_decoding(policy, monkeypatch):
    monkeypatch.setattr(api, "decode_image_bytes", lambda *args: pytest.fail("Invalid policies must not decode"))
    with TestClient(api.app) as client:
        response = post(client, policy)
    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_DIAGNOSTIC_POLICY"


def test_policy_and_image_byte_limits(monkeypatch):
    with TestClient(api.app) as client:
        response = post(client, " " * 8193)
        assert response.status_code == 413
        assert response.json()["error_code"] == "DIAGNOSTIC_POLICY_TOO_LARGE"
        monkeypatch.setattr(api, "MAX_UPLOAD_BYTES", 10)
        assert post(client).json()["error_code"] == "FILE_TOO_LARGE"


def test_header_pixels_are_checked_before_decode(monkeypatch):
    monkeypatch.setattr(api, "MAX_IMAGE_PIXELS", 100)
    monkeypatch.setattr(api, "decode_image_bytes", lambda *args: pytest.fail("Header limit must reject before decode"))
    with TestClient(api.app) as client:
        response = post(client)
    assert response.status_code == 413 and response.json()["error_code"] == "IMAGE_TOO_LARGE"


def test_shared_slot_busy_and_recovery_after_policy_image_failures(monkeypatch):
    slots = BoundedSemaphore(1)
    monkeypatch.setattr(api, "_analysis_slots", slots)
    slots.acquire()
    with TestClient(api.app) as client:
        busy = post(client)
        assert busy.status_code == 503 and busy.headers["Retry-After"] == "1"
        slots.release()
        assert post(client, content=b"").json()["error_code"] == "EMPTY_IMAGE"
        assert post(client, content=b"broken").status_code == 400
        mismatch = post(client, '{"min_laplacian_score":100,"sharpness_intensity_max":65535}')
        assert mismatch.status_code == 400 and mismatch.json()["error_code"] == "INVALID_DIAGNOSTIC_INPUT"
        assert post(client).status_code == 200
        assert client.post("/api/blur/check", files={"image": ("ok.png", encoded(), "image/png")} ).status_code == 200


def test_diagnostics_accepts_tiny_images_without_heatmap_grid_constraints():
    with TestClient(api.app) as client:
        payload = post(client, content=encoded(np.zeros((1, 1), dtype=np.uint8))).json()
    assert payload["measurements"]["resolution"]["pixels"] == 1
    assert payload["checks"]["sharpness"]["status"] == "insufficient_evidence"
    assert not any(check["status"] == "warning" for check in payload["checks"].values())


def test_exif_oriented_resolution_matches_preview():
    image = Image.fromarray(np.tile(np.arange(160, dtype=np.uint8), (128, 1)))
    exif = image.getexif()
    exif[274] = 6
    stream = BytesIO()
    image.save(stream, format="JPEG", exif=exif)
    expected = diagnose_image_quality(np.asarray(ImageOps.exif_transpose(Image.open(BytesIO(stream.getvalue())))))
    with TestClient(api.app) as client:
        response = post(client, content=stream.getvalue(), filename="rotated.jpg")
    assert response.status_code == 200
    assert response.json()["measurements"] == expected["measurements"]
    assert (response.json()["width"], response.json()["height"]) == (128, 160)


@pytest.mark.parametrize("chunked", [False, True])
def test_diagnostic_request_stream_limit(chunked):
    body = b"x" * (api.MAX_UPLOAD_BYTES + api.MULTIPART_OVERHEAD_BYTES + 1)
    content = (body[i:i + 65536] for i in range(0, len(body), 65536)) if chunked else body
    with TestClient(api.app) as client:
        response = client.post(ROUTE, content=content, headers={"Content-Type": "multipart/form-data; boundary=boundary"})
    assert response.status_code == 413 and response.json()["error_code"] == "REQUEST_TOO_LARGE"
