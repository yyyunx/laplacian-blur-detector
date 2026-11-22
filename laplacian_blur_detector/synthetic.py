"""Versioned synthetic stress cases, not human-labeled image-quality validation."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import cv2
import numpy as np

CASES = ("sharp", "gaussian_blur", "motion_blur", "partial_blur", "low_texture", "noise_contamination")
GENERATOR_VERSION = 1


def preview_image() -> np.ndarray:
    y, x = np.indices((512, 256))
    crisp = (((x // 8 + y // 8) % 2) * 200 + 25).astype(np.uint8)
    return np.concatenate([crisp, cv2.GaussianBlur(crisp, (15, 15), 3), np.full_like(crisp, 125)], axis=1)


def _source(rng: np.random.Generator) -> np.ndarray:
    image = np.full((256, 384), int(rng.integers(185, 235)), dtype=np.uint8)
    ink = int(rng.integers(15, 65))
    for line in range(5):
        text = f"Pattern {rng.integers(10000, 99999)}"
        cv2.putText(image, text, (18 + int(rng.integers(0, 8)), 40 + 43 * line), cv2.FONT_HERSHEY_SIMPLEX, 0.75, ink, 2)
    for _ in range(9):
        center = tuple(int(v) for v in rng.integers((15, 15), (370, 245)))
        cv2.circle(image, center, int(rng.integers(3, 12)), ink, 1)
    return image


def generate_dataset(output: Path, seed: int = 2026, samples_per_case: int = 4) -> Path:
    """Each source capture and all its derived variants belong to one split."""
    if output.exists():
        raise ValueError("Synthetic dataset output already exists; choose a new directory.")
    if not 1 <= samples_per_case <= 100:
        raise ValueError("Samples per case must be between 1 and 100.")
    rng = np.random.default_rng(seed)
    output.mkdir(parents=True)
    rows = []
    for split_index, split in enumerate(("calibration", "test")):
        for index in range(samples_per_case):
            source = _source(rng)
            gaussian = cv2.GaussianBlur(source, (25, 25), 4)
            kernel = np.zeros((17, 17), dtype=np.float64)
            kernel[8, :] = 1 / 17
            partial = source.copy()
            partial[:, 192:] = cv2.GaussianBlur(source, (31, 31), 6)[:, 192:]
            noisy = np.clip(gaussian.astype(np.float64) + rng.normal(0, 25, source.shape), 0, 255).astype(np.uint8)
            # Unique flat intensities prevent duplicate encoded images across captures.
            flat_value = 25 + split_index * 110 + index
            variants = (source, gaussian, cv2.filter2D(source, -1, kernel), partial,
                        np.full_like(source, flat_value), noisy)
            for case, image in zip(CASES, variants):
                filename = f"{split}-{index:03d}-{case}.png"
                if not cv2.imwrite(str(output / filename), image):
                    raise OSError(f"Could not write {filename}")
                rows.append({
                    "filename": filename, "label": "usable" if case in ("sharp", "low_texture") else "retake",
                    "split": split, "group": f"synthetic-{split}-capture-{index}",
                    "domain": "synthetic", "reason": case,
                })
    manifest = output / "labels.csv"
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["filename", "label", "split", "group", "domain", "reason"])
        writer.writeheader()
        writer.writerows(rows)
    metadata = {
        "generator_version": GENERATOR_VERSION, "seed": seed, "samples_per_case_per_split": samples_per_case,
        "cases": list(CASES), "samples": len(rows), "runtime": {"numpy": np.__version__, "opencv": cv2.__version__},
        "parameters": {"gaussian_kernel": 25, "gaussian_sigma": 4, "motion_kernel_horizontal": 17,
                       "partial_blur": "right_half_kernel31_sigma6", "noise_sigma": 25},
        "label_rule": "sharp and intentionally flat content are usable; induced blur and blurred-plus-noise are retake",
        "evidence": "synthetic_experiment_only_not_human_labels_or_real_world_accuracy",
        "license": "Generated entirely by project code; MIT. No external images or personal data.",
    }
    (output / "dataset.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return manifest
