"""One-command synthetic experiment and static visualization demo."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import cv2
import numpy as np

from .benchmark import main as benchmark_main
from .sharpness import analyze_local_sharpness
from .synthetic import generate_dataset, preview_image


def render_heatmap(image: np.ndarray, metric: str, opacity: float = 0.55) -> np.ndarray:
    """Static measurement illustration with the same relative/hatching rules as UI."""
    cells = analyze_local_sharpness(image, (8, 12), metric)
    eligible = [cell["sharpness_score"] for cell in cells if not cell["is_low_texture"]]
    minimum, maximum = (min(eligible), max(eligible)) if eligible else (0, 0)
    rgb = np.array([[49, 54, 149], [32, 178, 170], [253, 231, 37]], dtype=np.float64)
    overlay = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    for cell in cells:
        x, y, w, h = (cell[key] for key in ("x", "y", "width", "height"))
        region = overlay[y:y + h, x:x + w]
        if cell["is_low_texture"]:
            region[:] = (85, 65, 51)
            yy, xx = np.indices((h, w))
            region[(xx + yy) % 12 < 3] = (252, 250, 248)
        else:
            value = 0.5 if maximum == minimum else (cell["sharpness_score"] - minimum) / (maximum - minimum)
            index = 0 if value < 0.5 else 1
            color = rgb[index] + (rgb[index + 1] - rgb[index]) * ((value - index * 0.5) * 2)
            region[:] = np.rint(color[::-1]).astype(np.uint8)
    return cv2.addWeighted(cv2.cvtColor(image, cv2.COLOR_GRAY2BGR), 1 - opacity, overlay, opacity, 0)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/full-demo"), help="New output directory")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--samples-per-case", type=int, default=4)
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise ValueError("Demo output already exists; choose a new --output directory.")
        if not 1 <= args.samples_per_case <= 100:
            raise ValueError("Samples per case must be between 1 and 100.")
        manifest = generate_dataset(args.output / "dataset", args.seed, args.samples_per_case)
        image = preview_image()
        for name, pixels in (("original", image), ("laplacian-heatmap", render_heatmap(image, "laplacian")),
                             ("tenengrad-heatmap", render_heatmap(image, "tenengrad"))):
            if not cv2.imwrite(str(args.output / f"{name}.png"), pixels):
                raise OSError(f"Could not write {name}.png")
        result = benchmark_main([str(manifest), "--compare", "--calibrate", "--output", str(args.output / "comparison")])
        if result:
            return result
        print("Synthetic experiment only: labels are generation rules, not human accuracy judgments.")
        print(f"Open {args.output / 'comparison' / 'metric-comparison.svg'} and the original/heatmap PNGs.")
        return 0
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
