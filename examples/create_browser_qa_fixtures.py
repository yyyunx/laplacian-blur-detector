"""Create owned, asymmetric manual-QA images and EXIF display references."""

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

from laplacian_blur_detector.synthetic import preview_image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/browser-qa"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    image = cv2.resize(preview_image(), (1027, 773), interpolation=cv2.INTER_NEAREST)
    for text, position, color in (("TOP LEFT", (15, 45), (0, 0, 255)),
                                  ("BOTTOM RIGHT", (650, 735), (255, 0, 0))):
        cv2.putText(image, text, position, cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
    assert cv2.imwrite(str(args.output / "odd-landscape.png"), image)
    assert cv2.imwrite(str(args.output / "portrait.png"), cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE))
    for name, value in (("flat", 128), ("dark", 0), ("white", 255)):
        assert cv2.imwrite(str(args.output / (name + ".png")), np.full((256, 384, 3), value, dtype=np.uint8))
    source = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    for orientation in range(2, 9):
        exif = source.getexif()
        exif[274] = orientation
        path = args.output / f"exif-{orientation}.jpg"
        source.save(path, quality=90, exif=exif)
        with Image.open(path) as decoded:
            ImageOps.exif_transpose(decoded).save(args.output / f"reference-exif-{orientation}.png")
    print(f"Created synthetic QA fixtures and display references in {args.output}")


if __name__ == "__main__":
    main()
