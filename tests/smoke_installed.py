"""Run explicitly after installing a wheel, from outside the source checkout."""

import csv
from pathlib import Path
import subprocess
import sys
import sysconfig
import tempfile

import cv2
from fastapi.testclient import TestClient
import numpy as np

import laplacian_blur_detector
from laplacian_blur_detector.api import app


def run_command(name: str, *args: str) -> None:
    suffix = ".exe" if sys.platform == "win32" else ""
    command = Path(sysconfig.get_path("scripts")) / (name + suffix)
    subprocess.run([str(command), *args], check=True, timeout=30)


def main() -> None:
    package_dir = Path(laplacian_blur_detector.__file__).resolve().parent
    checkout_package = Path(__file__).resolve().parents[1] / "laplacian_blur_detector"
    assert package_dir != checkout_package, "Smoke check must use an installed wheel."
    subprocess.run(
        [sys.executable, "-c", (
            "import sys; "
            "sys.modules['fastapi'] = None; sys.modules['uvicorn'] = None; "
            "from laplacian_blur_detector import calculate_blur_score; "
            "import numpy as np; "
            "assert calculate_blur_score(np.zeros((8, 8), dtype=np.uint8)) == 0"
        )],
        check=True,
        timeout=30,
    )
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        image = root / "sample.png"
        assert cv2.imwrite(str(image), np.zeros((32, 32), dtype=np.uint8))
        output = root / "scores.csv"
        run_command("laplacian-blur", str(image))
        run_command("laplacian-blur-evaluate", str(root), "--output", str(output))
        with output.open(newline="", encoding="utf-8") as stream:
            assert len(list(csv.DictReader(stream))) == 1
        run_command("laplacian-blur-serve", "--help")
        manifest = root / "labels.csv"
        manifest.write_text(
            "filename,label,split,group,domain\nsample.png,retake,test,smoke,photos\n",
            encoding="utf-8",
        )
        run_command("laplacian-blur-benchmark", str(manifest), "--output", str(root / "benchmark"))
        assert (root / "benchmark" / "summary.json").is_file()
        with TestClient(app) as client:
            assert client.get("/healthz").json() == {"status": "ok"}
            assert "Laplacian Blur Detector" in client.get("/").text
            for asset in ("app.js", "styles.css"):
                assert client.get(f"/static/{asset}").status_code == 200
            response = client.post(
                "/api/blur/check",
                files={"image": ("sample.png", image.read_bytes(), "image/png")},
            )
            assert response.status_code == 200
            assert response.json()["is_blurry"] is True
    print(f"Installed package smoke checks passed: {package_dir}")


if __name__ == "__main__":
    main()
