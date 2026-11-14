"""Recursively score supported images in a dataset directory."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from .blur_detector import detect_blur
from .config import DEFAULT_BLUR_THRESHOLD
from .image_utils import SUPPORTED_IMAGE_EXTENSIONS, load_image


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Evaluate blur scores for a directory.")
    parser.add_argument("directory", type=Path, help="Folder to scan recursively")
    parser.add_argument("--threshold", type=float, default=DEFAULT_BLUR_THRESHOLD)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs") / "blur_scores.csv",
        help="CSV output path",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Write blur metrics for every readable supported image to a CSV file."""
    args = parse_args(argv)
    if not args.directory.is_dir():
        print(f"Error: Dataset directory does not exist: {args.directory}", file=sys.stderr)
        return 1

    image_paths = sorted(
        path
        for path in args.directory.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    )
    rows: list[dict[str, str | int | float | bool]] = []
    for image_path in image_paths:
        try:
            image = load_image(image_path)
            result = detect_blur(image, args.threshold)
        except ValueError as error:
            print(f"Skipping {image_path}: {error}", file=sys.stderr)
            continue
        height, width = image.shape[:2]
        rows.append(
            {
                "filename": image_path.relative_to(args.directory).as_posix(),
                "width": width,
                "height": height,
                "file_size": image_path.stat().st_size,
                **result,
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "filename",
        "width",
        "height",
        "file_size",
        "blur_score",
        "threshold",
        "is_blurry",
    ]
    with args.output.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} image scores to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
