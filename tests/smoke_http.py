"""Live HTTP smoke for a local installed service or container; stdlib only."""

import argparse
import json
from pathlib import Path
import time
from urllib.error import URLError
from urllib.request import Request, urlopen


def wait_for_health(base, timeout=30, interval=0.25):
    """Wait through transient startup resets, while preserving the health contract."""
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Service did not become healthy before the deadline")
        try:
            with urlopen(base + "/healthz", timeout=min(5, remaining)) as response:
                assert response.status == 200
                assert json.load(response) == {"status": "ok"}
            return
        except (URLError, ConnectionError, TimeoutError) as error:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Service did not become healthy before the deadline") from error
            time.sleep(min(interval, remaining))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--image", type=Path, default=Path(__file__).resolve().parents[1] / "web/demo.png")
    args = parser.parse_args()
    base = args.url.rstrip("/")

    def get(path):
        with urlopen(base + path, timeout=10) as response:
            assert response.status == 200
            return response.read()

    wait_for_health(base)
    assert b"Laplacian Blur Detector" in get("/")
    for asset in ("app.js", "heatmap.js", "quality-diagnostics.js", "styles.css", "demo.png"):
        assert get("/static/" + asset)
    config = json.loads(get("/api/config"))
    assert config["max_image_pixels"] == 20_000_000
    image = args.image.read_bytes()

    def post(path, fields=None, files=None):
        boundary = "sharpness-smoke-boundary"
        parts = []
        for name, value in (fields or {}).items():
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
        for field, content in (files or [("image", image)]):
            parts.extend([f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"; filename="demo.png"\r\nContent-Type: image/png\r\n\r\n'.encode(), content, b"\r\n"])
        parts.append(f"--{boundary}--\r\n".encode())
        request = Request(base + path, data=b"".join(parts), headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        with urlopen(request, timeout=15) as response:
            assert response.status == 200
            return json.load(response)

    legacy = post("/api/blur/check")
    assert set(legacy) == {"success", "filename", "width", "height", "file_size", "blur_score", "threshold", "is_blurry", "processing_ms", "message"}
    assert legacy["success"]
    for metric in ("laplacian", "tenengrad"):
        local = post("/api/sharpness/local", {"metric": metric})
        assert local["success"] and local["metric"] == metric and len(local["cells"]) == 64
        assert local["coordinate_space"] == "exif_oriented_pixels"
        assert any(cell["is_low_texture"] for cell in local["cells"])
    quality = post("/api/quality/diagnose", {"policy": '{"min_width":100000}'})
    assert quality["checks"]["resolution"]["status"] == "warning"
    assert "accepted" not in quality
    batch = post("/api/blur/batch", files=[("images", image), ("images", b"invalid")])
    assert (batch["total"], batch["processed"], batch["failed"]) == (2, 1, 1)
    print("Live HTTP smoke passed: assets, legacy contract/batch, both local metrics, quality policy")


if __name__ == "__main__":
    main()
