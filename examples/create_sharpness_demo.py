"""Generate a local-only crisp / softened / flat heatmap fixture."""

import argparse
from pathlib import Path

import cv2
import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/sharpness-demo.png"))
    args = parser.parse_args()
    y, x = np.indices((512, 256))
    pattern = (((x // 8 + y // 8) % 2) * 200 + 25).astype(np.uint8)
    image = np.concatenate([pattern, cv2.GaussianBlur(pattern, (15, 15), 3), np.full_like(pattern, 125)], axis=1)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(args.output), image):
        raise RuntimeError(f"Could not write {args.output}")
    print(f"Wrote {args.output}: crisp, Gaussian softened, and flat content.")


if __name__ == "__main__":
    main()
