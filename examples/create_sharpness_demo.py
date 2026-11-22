"""Generate a local-only sharp / softened / flat fixture for the heatmap demo."""

import argparse
from pathlib import Path

import cv2
from laplacian_blur_detector.synthetic import preview_image


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/sharpness-demo.png"))
    args = parser.parse_args()
    image = preview_image()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(args.output), image):
        raise RuntimeError(f"Could not write {args.output}")
    print(f"Wrote {args.output}: left=crisp pattern, middle=Gaussian softened, right=flat content.")


if __name__ == "__main__":
    main()
