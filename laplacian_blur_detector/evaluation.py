"""Classification metrics and calibration independent of image I/O or HTTP."""

from __future__ import annotations

from itertools import groupby
from fractions import Fraction
import math
from typing import Sequence


def finite_nonnegative(value: float) -> float:
    """Resolve a score/threshold without allowing NaN, infinity, or negatives."""
    try:
        resolved = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("Scores and thresholds must be finite non-negative numbers.") from error
    if not math.isfinite(resolved) or resolved < 0:
        raise ValueError("Scores and thresholds must be finite non-negative numbers.")
    return resolved


def _validated_pairs(scores: Sequence[float], labels: Sequence[str]) -> list[tuple[float, str]]:
    if len(scores) == 0 or len(scores) != len(labels):
        raise ValueError("Scores and labels must have the same non-zero length.")
    if any(label not in {"usable", "retake"} for label in labels):
        raise ValueError("Labels must be 'usable' or 'retake'.")
    return [(finite_nonnegative(score), label) for score, label in zip(scores, labels)]


def _metrics(usable: int, retake: int, false_reject: int, missed_retake: int) -> dict:
    true_retake = retake - missed_retake
    true_usable = usable - false_reject
    rejected = true_retake + false_reject
    false_reject_rate = false_reject / usable if usable else None
    missed_retake_rate = missed_retake / retake if retake else None
    f1_denominator = 2 * true_retake + false_reject + missed_retake
    return {
        "samples": usable + retake,
        "actual_usable": usable,
        "actual_retake": retake,
        "confusion": {
            "true_retake": true_retake,
            "false_reject": false_reject,
            "missed_retake": missed_retake,
            "true_usable": true_usable,
        },
        "false_reject_rate": false_reject_rate,
        "missed_retake_rate": missed_retake_rate,
        "retake_precision": true_retake / rejected if rejected else None,
        "retake_recall": true_retake / retake if retake else None,
        "retake_f1": 2 * true_retake / f1_denominator if f1_denominator else None,
        "accuracy": (true_retake + true_usable) / (usable + retake),
        "balanced_accuracy": (
            1 - (false_reject_rate + missed_retake_rate) / 2
            if usable and retake else None
        ),
    }


def classification_metrics(
    scores: Sequence[float], labels: Sequence[str], threshold: float,
) -> dict:
    """Treat retake as positive; equality with the threshold predicts usable."""
    pairs = _validated_pairs(scores, labels)
    threshold = finite_nonnegative(threshold)
    usable = sum(label == "usable" for _, label in pairs)
    retake = len(pairs) - usable
    false_reject = sum(label == "usable" and score < threshold for score, label in pairs)
    missed_retake = sum(label == "retake" and score >= threshold for score, label in pairs)
    return _metrics(usable, retake, false_reject, missed_retake)


def calibrate_threshold(
    scores: Sequence[float], labels: Sequence[str],
    false_reject_cost: float = 1, missed_retake_cost: float = 1,
) -> tuple[float, list[dict]]:
    """Sweep distinct decisions in O(n log n), using calibration labels only.

    Minimize the weighted mean of the two class error rates. Ties prefer fewer
    missed retakes, then the lower threshold. Equal scores always move together.
    """
    pairs = sorted(_validated_pairs(scores, labels))
    costs = (float(false_reject_cost), float(missed_retake_cost))
    if any(not math.isfinite(cost) or cost <= 0 for cost in costs):
        raise ValueError("Calibration costs must be finite positive numbers.")
    reject_weight, missed_weight = (Fraction(cost) for cost in costs)
    usable = sum(label == "usable" for _, label in pairs)
    retake = len(pairs) - usable
    if not usable or not retake:
        raise ValueError("Calibration requires both usable and retake labels in each domain.")
    false_reject, missed_retake = 0, retake
    curve: list[dict] = []
    best_key: tuple[Fraction, int, float] | None = None
    best_threshold = 0.0
    denominator = (reject_weight + missed_weight) * usable * retake

    def record(threshold: float) -> None:
        nonlocal best_key, best_threshold
        # Exact comparison preserves the documented tie break even when float
        # rounding makes mathematically equal error rates look different.
        weighted_errors = reject_weight * false_reject * retake + missed_weight * missed_retake * usable
        key = (weighted_errors, missed_retake, threshold)
        if best_key is None or key < best_key:
            best_key, best_threshold = key, threshold
        curve.append({
            "threshold": threshold,
            "false_reject": false_reject,
            "missed_retake": missed_retake,
            "weighted_class_error": float(weighted_errors / denominator),
        })

    record(0.0)
    groups = [(score, list(items)) for score, items in groupby(pairs, key=lambda pair: pair[0])]
    for index, (score, items) in enumerate(groups):
        false_reject += sum(label == "usable" for _, label in items)
        missed_retake -= sum(label == "retake" for _, label in items)
        if index + 1 < len(groups):
            next_score = groups[index + 1][0]
            midpoint = score + (next_score - score) / 2
            # Adjacent floats can round their midpoint to the lower score.
            threshold = midpoint if midpoint > score else next_score
        else:
            threshold = math.nextafter(score, math.inf)
        if math.isfinite(threshold):
            record(threshold)
    return best_threshold, curve
