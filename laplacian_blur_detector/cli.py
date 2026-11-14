"""Run the blur detector against one image from the command line."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .blur_detector import detect_blur
from .config import DEFAULT_BLUR_THRESHOLD
from .image_utils import load_image


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Check whether an image is blurry.")
    parser.add_argument("image", type=Path, help="Path to a JPG, JPEG, or PNG image")
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_BLUR_THRESHOLD,
        help=f"Blur threshold (default: {DEFAULT_BLUR_THRESHOLD:g})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Load, score, and print one image's blur classification."""
    args = parse_args(argv)
    try:
        image = load_image(args.image)
        result = detect_blur(image, args.threshold)
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Image: {args.image.name}")
    height, width = image.shape[:2]
    print(f"Resolution: {width} x {height}")
    print(f"Blur score: {result['blur_score']:.2f}")
    print(f"Threshold: {result['threshold']:.2f}")
    print(f"Result: {'BLURRY' if result['is_blurry'] else 'CLEAR'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
