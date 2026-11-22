"""Interpretable image measurements and opt-in, application-owned diagnostic hints."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
import math
from numbers import Real
from typing import Mapping

import numpy as np

from .sharpness import _prepare_grayscale, calculate_sharpness


def _finite_real(name: str, value: Real) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number.")
    try:
        resolved = float(value)
    except (ValueError, TypeError, OverflowError) as error:
        raise ValueError(f"{name} must be a finite number.") from error
    if not math.isfinite(resolved):
        raise ValueError(f"{name} must be a finite number.")
    return resolved


@dataclass(frozen=True)
class DiagnosticPolicy:
    """Measurement cutoffs plus optional warning limits, never a universal gate.

    Brightness/texture/cutoffs use normalized encoded intensity (0..1). Sharpness
    limits use native input units and require an explicit intensity-scale pin.
    None disables a warning rule. See docs/DIAGNOSTICS.md for exact definitions.
    """

    dark_pixel_cutoff: float = 16 / 255
    bright_pixel_cutoff: float = 250 / 255
    min_texture_std: float = 5 / 255
    min_mean_brightness: float | None = None
    max_dark_ratio: float | None = None
    max_bright_ratio: float | None = None
    min_width: int | None = None
    min_height: int | None = None
    min_laplacian_score: float | None = None
    min_tenengrad_score: float | None = None
    sharpness_intensity_max: float | None = None

    def __post_init__(self) -> None:
        for name in ("dark_pixel_cutoff", "bright_pixel_cutoff", "min_texture_std",
                     "min_mean_brightness", "max_dark_ratio", "max_bright_ratio"):
            value = getattr(self, name)
            if value is None and name in ("min_mean_brightness", "max_dark_ratio", "max_bright_ratio"):
                continue
            value = _finite_real(name, value)
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be a finite number between 0 and 1.")
            object.__setattr__(self, name, float(value))
        if self.dark_pixel_cutoff >= self.bright_pixel_cutoff:
            raise ValueError("dark_pixel_cutoff must be less than bright_pixel_cutoff.")
        for name in ("min_width", "min_height"):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value <= 0):
                raise ValueError(f"{name} must be a positive integer or None.")
        for name in ("min_laplacian_score", "min_tenengrad_score", "sharpness_intensity_max"):
            value = getattr(self, name)
            if value is None:
                continue
            value = _finite_real(name, value)
            if value < 0:
                raise ValueError(f"{name} must be finite and non-negative or None.")
            object.__setattr__(self, name, float(value))
        if self.sharpness_intensity_max is not None and self.sharpness_intensity_max not in (1, 255, 65535):
            raise ValueError("sharpness_intensity_max must be 1, 255, or 65535.")
        if (self.min_laplacian_score is not None or self.min_tenengrad_score is not None) and self.sharpness_intensity_max is None:
            raise ValueError("Sharpness warning limits require sharpness_intensity_max to pin their native units.")

    @classmethod
    def from_mapping(cls, value: Mapping) -> DiagnosticPolicy:
        if not isinstance(value, Mapping):
            raise ValueError("Diagnostic policy must be an object.")
        unknown = set(value) - {field.name for field in fields(cls)}
        if unknown:
            raise ValueError("Unknown diagnostic policy fields: " + ", ".join(sorted(map(str, unknown))))
        return cls(**value)


def measure_image_quality(
    image: np.ndarray, *, dark_pixel_cutoff: float = 16 / 255,
    bright_pixel_cutoff: float = 250 / 255,
) -> dict:
    """Measure brightness/exposure/resolution and existing native sharpness metrics.

    uint8/uint16 inputs use their dtype range, not image min/max. Float inputs
    must already be in 0..1. Color is OpenCV BGR/BGRA; alpha is ignored. This is
    encoded intensity, not physical luminance or sensor exposure reconstruction.
    """
    cutoffs = DiagnosticPolicy(dark_pixel_cutoff=dark_pixel_cutoff, bright_pixel_cutoff=bright_pixel_cutoff)
    gray = _prepare_grayscale(image)
    scale = 255.0 if image.dtype == np.uint8 else 65535.0 if image.dtype == np.uint16 else 1.0
    channels = image[:, :, :3] if image.ndim == 3 and image.shape[2] in (3, 4) else gray
    if scale == 1 and (not np.isfinite(channels).all() or channels.min() < 0 or channels.max() > 1):
        raise ValueError("Float diagnostic images must have finite non-alpha values in 0..1.")
    height, width = gray.shape
    bright_limit = cutoffs.bright_pixel_cutoff * scale
    if channels.ndim == 3:
        bright_pixels = channels[:, :, 0] >= bright_limit
        for channel in range(1, channels.shape[2]):
            np.logical_or(bright_pixels, channels[:, :, channel] >= bright_limit, out=bright_pixels)
    else:
        bright_pixels = channels >= bright_limit
    bright_ratio = float(np.count_nonzero(bright_pixels) / gray.size)
    del bright_pixels  # Release the full-image mask before either derivative pass.
    texture_std = float(gray.std())
    return {
        "brightness": {"mean": float(gray.mean() / scale), "median": float(np.median(gray) / scale),
                       "unit": "normalized_encoded_grayscale"},
        "exposure": {
            "dark_pixel_ratio": float(np.count_nonzero(gray <= cutoffs.dark_pixel_cutoff * scale) / gray.size),
            "bright_pixel_ratio": bright_ratio,
            "dark_pixel_cutoff": cutoffs.dark_pixel_cutoff, "bright_pixel_cutoff": cutoffs.bright_pixel_cutoff,
            "bright_pixel_definition": "any_non_alpha_channel_at_or_above_cutoff",
        },
        "resolution": {"width": width, "height": height, "pixels": width * height},
        "sharpness": {"laplacian_score": calculate_sharpness(gray, "laplacian"),
                      "tenengrad_score": calculate_sharpness(gray, "tenengrad"),
                      "texture_std": texture_std, "texture_std_normalized": texture_std / scale,
                      "input_intensity_max": scale},
    }


def _check(status: str, message: str, limitation: str, suggestion: str | None = None) -> dict:
    return {"status": status, "message": message, "suggestion": suggestion, "limitation": limitation}


def diagnose_image_quality(image: np.ndarray, policy: DiagnosticPolicy | None = None) -> dict:
    """Apply explicit policy hints without accepting/rejecting the image."""
    if policy is None:
        policy = DiagnosticPolicy()
    if not isinstance(policy, DiagnosticPolicy):
        raise ValueError("Use a DiagnosticPolicy instance or DiagnosticPolicy.from_mapping().")
    measurements = measure_image_quality(image, dark_pixel_cutoff=policy.dark_pixel_cutoff, bright_pixel_cutoff=policy.bright_pixel_cutoff)
    brightness, exposure = measurements["brightness"], measurements["exposure"]
    resolution, sharpness = measurements["resolution"], measurements["sharpness"]
    if policy.sharpness_intensity_max is not None and policy.sharpness_intensity_max != sharpness["input_intensity_max"]:
        raise ValueError("Policy sharpness_intensity_max does not match the image dtype scale; recalibrate or change the policy.")
    checks = {}
    rules = (
        ("brightness", policy.min_mean_brightness, brightness["mean"], "below", "Mean brightness is below the configured limit.",
         "Increase lighting or review the capture exposure.", "Encoded grayscale is not physical luminance; a dark scene may be intentional."),
        ("underexposure", policy.max_dark_ratio, exposure["dark_pixel_ratio"], "above", "The dark-pixel ratio exceeds the configured limit.",
         "Add lighting or adjust capture exposure; inspect important shadow detail.", "Dark pixels may be legitimate background; the ratio cannot prove underexposure."),
        ("overexposure", policy.max_bright_ratio, exposure["bright_pixel_ratio"], "above", "Many pixels reach the configured bright cutoff in at least one color channel.",
         "Review exposure or lighting angle to preserve important highlight detail.", "Saturated colors or white backgrounds may be intentional; encoded values do not prove sensor clipping."),
    )
    for name, limit, value, direction, message, suggestion, limitation in rules:
        triggered = limit is not None and (value < limit if direction == "below" else value > limit)
        checks[name] = _check("not_evaluated" if limit is None else "warning" if triggered else "within_policy",
                              "Measured; no warning limit is configured." if limit is None else message if triggered else "The configured numeric limit is met; this is not an overall quality pass.",
                              limitation, suggestion if triggered else None)
    enabled_resolution = policy.min_width is not None or policy.min_height is not None
    small = (policy.min_width is not None and resolution["width"] < policy.min_width) or (policy.min_height is not None and resolution["height"] < policy.min_height)
    checks["resolution"] = _check("not_evaluated" if not enabled_resolution else "warning" if small else "within_policy",
                                  "Image dimensions are below the configured minimum." if small else "Dimensions measured; checks apply only to configured width/height limits.",
                                  "Pixel dimensions do not establish useful detail; upscaling does not recover captured information.",
                                  "Capture at a higher resolution or reduce cropping; avoid relying on upscaling." if small else None)
    low_texture = sharpness["texture_std_normalized"] <= policy.min_texture_std
    sharpness["is_low_texture"] = low_texture
    limits = (("laplacian_score", policy.min_laplacian_score), ("tenengrad_score", policy.min_tenengrad_score))
    below = [name for name, limit in limits if limit is not None and sharpness[name] < limit]
    has_limit = any(limit is not None for _, limit in limits)
    checks["sharpness"] = _check(
        "insufficient_evidence" if low_texture else "not_evaluated" if not has_limit else "warning" if below else "within_policy",
        "Low texture provides insufficient evidence to assess sharpness." if low_texture else "Below configured sharpness limits: " + ", ".join(below) if below else "Sharpness measured; only explicitly calibrated limits are evaluated.",
        "Content, noise, contrast and resizing affect both metrics; scores and thresholds are not interchangeable.",
        "Inspect a textured subject region; flat content is not automatically blurry." if low_texture else "Consider refocusing, stabilizing the camera, or reducing subject motion." if below else None,
    )
    checks["texture"] = _check("insufficient_evidence" if low_texture else "informational",
                               "Low texture; no sharpness rejection is made." if low_texture else "Intensity variation is above the configured texture cutoff.",
                               "Standard deviation is a contrast proxy; gradients and noise can raise it without useful fine detail.")
    return {"schema_version": 1, "measurements": measurements, "checks": checks, "policy": asdict(policy),
            "limitations": ["Measurements and hints are not a complete image-quality assessment or an acceptance decision.",
                            "Alpha is ignored; hidden RGB values in transparent pixels can affect measurements."]}
