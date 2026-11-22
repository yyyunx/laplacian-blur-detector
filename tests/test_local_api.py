"""Local endpoint measurements, bounded resources, and legacy HTTP contracts."""

from io import BytesIO
from threading import BoundedSemaphore

import cv2
import numpy as np
from PIL import Image
import pytest
from fastapi.testclient import TestClient

from laplacian_blur_detector import api, analyze_local_sharpness

ROUTE = "/api/sharpness/local"


def encoded(image):
    ok, buffer = cv2.imencode(".png", image)
    assert ok
    return buffer.tobytes()


def post(client, data=None, content=None, name="sample.png"):
    if content is None:
        content = encoded(np.zeros((128, 128), dtype=np.uint8))
    return client.post(ROUTE, data=data or {}, files={"image": (name, content, "image/png")})


@pytest.mark.parametrize("metric", ["laplacian", "tenengrad"])
def test_endpoint_matches_core_with_non_divisible_dimensions(metric):
    image = np.random.default_rng(0).integers(0, 256, (133, 149), dtype=np.uint8)
    with TestClient(api.app) as client:
        response = post(client, {"metric": metric, "grid_rows": 3, "grid_columns": 5, "min_texture_std": 9}, encoded(image))
    assert response.status_code == 200
    payload = response.json()
    assert payload["cells"] == analyze_local_sharpness(image, (3, 5), metric, min_texture_std=9)
    assert payload["width"] == 149 and payload["height"] == 133
    assert payload["coordinate_space"] == "exif_oriented_pixels"
    assert payload["metric"] == metric and payload["min_texture_std"] == 9
    assert "is_blurry" not in payload


def test_defaults_and_response_size_bound():
    with TestClient(api.app) as client:
        result = post(client).json()
        assert len(result["cells"]) == 64
        assert all(cell["is_low_texture"] and cell["sharpness_score"] == 0 for cell in result["cells"])
        large = post(client, {"grid_rows": 32, "grid_columns": 32}, encoded(np.zeros((512, 512), dtype=np.uint8)))
        assert large.status_code == 200
        assert len(large.json()["cells"]) == 1024
        assert len(large.content) < 300_000


@pytest.mark.parametrize("data,code,status", [
    ({"metric": "invalid"}, "INVALID_METRIC", 400),
    ({"grid_rows": 33}, "INVALID_GRID", 400),
    ({"grid_columns": 0}, "INVALID_GRID", 400),
    ({"grid_columns": -1}, "INVALID_GRID", 400),
    ({"grid_rows": 9}, "GRID_TOO_FINE", 400),
    ({"min_texture_std": "nan"}, "INVALID_TEXTURE_CUTOFF", 400),
    ({"min_texture_std": "inf"}, "INVALID_TEXTURE_CUTOFF", 400),
    ({"min_texture_std": -1}, "INVALID_TEXTURE_CUTOFF", 400),
    ({"grid_rows": "1.5"}, None, 422),
])
def test_invalid_settings_are_rejected(data, code, status):
    with TestClient(api.app) as client:
        response = post(client, data)
    assert response.status_code == status
    if code:
        assert response.json()["error_code"] == code


def test_invalid_metric_and_grid_reject_before_decoding(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Invalid selectors must not decode an image")
    monkeypatch.setattr(api, "decode_image_bytes", forbidden)
    with TestClient(api.app) as client:
        assert post(client, {"metric": "bad"}).status_code == 400
        assert post(client, {"grid_rows": 33}).status_code == 400


def test_local_uses_shared_upload_and_header_limits(monkeypatch):
    content = encoded(np.zeros((128, 128), dtype=np.uint8))
    with TestClient(api.app) as client:
        monkeypatch.setattr(api, "MAX_UPLOAD_BYTES", 10)
        assert post(client, content=content).json()["error_code"] == "FILE_TOO_LARGE"
        monkeypatch.setattr(api, "MAX_UPLOAD_BYTES", 10 * 1024 * 1024)
        monkeypatch.setattr(api, "MAX_IMAGE_PIXELS", 100)
        monkeypatch.setattr(api, "decode_image_bytes", lambda *args: pytest.fail("Header must reject before decode"))
        response = post(client, content=content)
        assert response.status_code == 413
        assert response.json()["error_code"] == "IMAGE_TOO_LARGE"


@pytest.mark.parametrize("chunked", [False, True])
def test_local_request_stream_limit(chunked):
    body = b"x" * (api.MAX_UPLOAD_BYTES + api.MULTIPART_OVERHEAD_BYTES + 1)
    headers = {"Content-Type": "multipart/form-data; boundary=boundary"}
    content = (body[i:i + 65536] for i in range(0, len(body), 65536)) if chunked else body
    with TestClient(api.app) as client:
        response = client.post(ROUTE, content=content, headers=headers)
    assert response.status_code == 413
    assert response.json()["error_code"] == "REQUEST_TOO_LARGE"


def test_shared_busy_slot_and_failure_recovery(monkeypatch):
    slots = BoundedSemaphore(1)
    monkeypatch.setattr(api, "_analysis_slots", slots)
    slots.acquire()
    with TestClient(api.app) as client:
        response = post(client)
        assert response.status_code == 503
        assert response.headers["Retry-After"] == "1"
        slots.release()
        assert post(client, content=b"bad").status_code == 400
        assert post(client, {"grid_rows": 9}).status_code == 400
        assert post(client).status_code == 200
        # A legacy request uses the very same recovered slot.
        assert client.post("/api/blur/check", files={"image": ("ok.png", encoded(np.zeros((16, 16), dtype=np.uint8)), "image/png")}).status_code == 200


def test_renamed_gif_and_empty_upload_rejected():
    stream = BytesIO()
    Image.new("RGB", (128, 128)).save(stream, format="GIF")
    with TestClient(api.app) as client:
        assert post(client, content=stream.getvalue()).status_code == 400
        assert post(client, content=b"").json()["error_code"] == "EMPTY_IMAGE"


@pytest.mark.parametrize("orientation", [2, 3, 4, 5, 6, 7, 8])
def test_coordinates_match_browser_exif_orientation(orientation):
    y, x = np.indices((128, 160))
    pixels = ((x * 3 + y * 2) % 256).astype(np.uint8)
    source = Image.fromarray(pixels)
    exif = source.getexif()
    exif[274] = orientation
    stream = BytesIO()
    source.save(stream, format="JPEG", exif=exif)
    from PIL import ImageOps
    oriented = np.asarray(ImageOps.exif_transpose(Image.open(BytesIO(stream.getvalue()))))
    with TestClient(api.app) as client:
        response = post(client, {"grid_rows": 2, "grid_columns": 4}, stream.getvalue(), "oriented.jpg")
    assert response.status_code == 200
    result = response.json()
    assert (result["height"], result["width"]) == oriented.shape
    # JPEG grayscale decode agrees between Pillow/OpenCV for this fixture.
    assert result["cells"] == analyze_local_sharpness(oriented, (2, 4))


def test_legacy_result_keys_remain_exact():
    content = encoded(np.zeros((16, 16), dtype=np.uint8))
    keys = {"success", "filename", "width", "height", "file_size", "blur_score", "threshold", "is_blurry", "processing_ms", "message"}
    with TestClient(api.app) as client:
        single = client.post("/api/blur/check", files={"image": ("sample.png", content, "image/png")}).json()
        batch = client.post("/api/blur/batch", files={"images": ("sample.png", content, "image/png")}).json()
    assert set(single) == keys
    assert set(batch) == {"success", "total", "processed", "failed", "clear", "blurry", "threshold", "results"}
    assert set(batch["results"][0]) == keys
