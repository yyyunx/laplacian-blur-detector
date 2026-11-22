"""One-command packaged demo and preservation of existing output."""

import cv2

from laplacian_blur_detector.demo import main as demo_main

def test_demo_writes_real_artifacts_and_refuses_overwrite(tmp_path):
    output = tmp_path / "demo"
    assert demo_main(["--output", str(output), "--samples-per-case", "1"]) == 0
    for filename in ("original.png", "laplacian-heatmap.png", "tenengrad-heatmap.png"):
        image = cv2.imread(str(output / filename))
        assert image is not None and image.shape[:2] == (512, 768)
    original = (output / "comparison" / "comparison.json").read_bytes()
    assert demo_main(["--output", str(output)]) == 1
    assert original == (output / "comparison" / "comparison.json").read_bytes()
