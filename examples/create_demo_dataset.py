"""Generate non-personal demo images; this is a workflow demo, not an accuracy dataset."""

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New directory for synthetic images and labels.csv")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; choose a new directory.")
    args.output.mkdir(parents=True)
    rows = []
    rng = np.random.default_rng(2026)
    for domain in ("documents", "products"):
        for split in ("calibration", "test"):
            for label in ("usable", "retake"):
                image = rng.integers(225, 239, (320, 480, 3), dtype=np.uint8)
                if domain == "documents":
                    for index in range(6):
                        text = f"Sample line {index + 1}: {rng.integers(1000, 9999)}"
                        cv2.putText(image, text, (24, 42 + index * 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (30, 30, 30), 2)
                else:
                    color = tuple(int(value) for value in rng.integers(20, 170, 3))
                    cv2.rectangle(image, (100, 55), (380, 265), color, -1)
                    cv2.circle(image, (240, 160), int(rng.integers(45, 75)), (245, 245, 245), 4)
                    cv2.putText(image, "DEMO", (167, 173), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (245, 245, 245), 2)
                if label == "retake":
                    image = cv2.GaussianBlur(image, (21, 21), 0)
                filename = f"{domain}-{split}-{label}.png"
                if not cv2.imwrite(str(args.output / filename), image):
                    raise OSError(f"Could not write {filename}")
                rows.append({
                    "filename": filename, "label": label, "split": split,
                    "group": f"{domain}-{split}-{label}", "domain": domain,
                    "reason": "synthetic_gaussian_blur" if label == "retake" else "synthetic_sharp",
                })
    with (args.output / "labels.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["filename", "label", "split", "group", "domain", "reason"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Created {len(rows)} synthetic images and {args.output / 'labels.csv'}")
    print("Use this to try the workflow. Scores do not establish real-world accuracy.")


if __name__ == "__main__":
    main()
