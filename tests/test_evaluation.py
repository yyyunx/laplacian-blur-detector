"""Metric contracts and calibration checked against exhaustive decisions."""

import math
import random
from fractions import Fraction

import pytest

from laplacian_blur_detector.evaluation import calibrate_threshold, classification_metrics


def test_confusion_counts_and_threshold_equality() -> None:
    result = classification_metrics([10, 100, 90, 110], ["retake", "retake", "usable", "usable"], 100)
    assert result["confusion"] == {
        "true_retake": 1, "false_reject": 1, "missed_retake": 1, "true_usable": 1,
    }
    assert result["false_reject_rate"] == result["missed_retake_rate"] == 0.5
    assert result["retake_f1"] == result["accuracy"] == 0.5


def test_missing_class_is_reported_as_undefined_instead_of_perfect() -> None:
    result = classification_metrics([10], ["usable"], 0)
    assert result["false_reject_rate"] == 0
    assert result["missed_retake_rate"] is None
    assert result["retake_precision"] is None
    assert result["retake_recall"] is None
    assert result["balanced_accuracy"] is None


@pytest.mark.parametrize("scores,labels,threshold", [
    ([], [], 100), ([1], [], 100), ([1], ["unknown"], 100),
    ([math.nan], ["usable"], 100), ([math.inf], ["usable"], 100),
    ([-1], ["usable"], 100), ([1], ["usable"], math.nan),
    ([1], ["usable"], 10 ** 1000),
])
def test_metrics_reject_invalid_values(scores, labels, threshold) -> None:
    with pytest.raises(ValueError):
        classification_metrics(scores, labels, threshold)


@pytest.mark.parametrize("cost", [0, -1, math.nan, math.inf])
def test_calibration_rejects_invalid_costs(cost) -> None:
    with pytest.raises(ValueError, match="costs"):
        calibrate_threshold([1, 2], ["retake", "usable"], false_reject_cost=cost)


def test_calibration_requires_both_classes() -> None:
    with pytest.raises(ValueError, match="both"):
        calibrate_threshold([1], ["usable"])


def test_equal_scores_cannot_be_split_and_ties_prefer_fewer_missed_retakes() -> None:
    threshold, _ = calibrate_threshold([10, 10], ["retake", "usable"])
    result = classification_metrics([10, 10], ["retake", "usable"], threshold)
    assert result["confusion"]["missed_retake"] == 0
    assert result["confusion"]["false_reject"] == 1


def test_cost_weights_change_the_selected_decision() -> None:
    threshold, _ = calibrate_threshold([10, 10], ["retake", "usable"], false_reject_cost=10)
    assert threshold == 0


def test_sweep_matches_exhaustive_decisions_with_tied_scores() -> None:
    rng = random.Random(73)
    for _ in range(100):
        scores = [float(rng.randrange(8)) for _ in range(25)]
        labels = ["usable", "retake"] + [rng.choice(["usable", "retake"]) for _ in range(23)]
        reject_cost, missed_cost = rng.randint(1, 5), rng.randint(1, 5)
        threshold, _ = calibrate_threshold(scores, labels, reject_cost, missed_cost)

        def objective(candidate):
            metrics = classification_metrics(scores, labels, candidate)
            confusion = metrics["confusion"]
            loss = (
                Fraction(reject_cost * confusion["false_reject"], metrics["actual_usable"])
                + Fraction(missed_cost * confusion["missed_retake"], metrics["actual_retake"])
            )
            return loss, metrics["confusion"]["missed_retake"]

        candidates = [0, *sorted(set(scores)), math.nextafter(max(scores), math.inf)]
        expected_loss, expected_missed = min(objective(candidate) for candidate in candidates)
        actual_loss, actual_missed = objective(threshold)
        assert actual_loss == expected_loss
        assert actual_missed == expected_missed


def test_fractional_class_rates_keep_the_documented_tie_break() -> None:
    scores = [8, 0, 1, 3, 5, 7, 8, 2, 4, 1, 7, 1, 1, 0, 4, 5, 5, 7, 0, 6, 0, 2, 1, 3, 1, 0]
    labels = ["usable" if index in {0, 3, 4, 5, 8, 12, 13, 15, 17, 18, 20, 21, 25} else "retake" for index in range(26)]
    threshold, _ = calibrate_threshold(scores, labels, 6, 5)
    assert classification_metrics(scores, labels, threshold)["confusion"]["missed_retake"] < 13


def test_adjacent_float_scores_use_a_representable_boundary() -> None:
    sharp = math.nextafter(1.0, math.inf)
    threshold, _ = calibrate_threshold([1.0, sharp], ["retake", "usable"])
    assert threshold == sharp
    assert classification_metrics([1.0, sharp], ["retake", "usable"], threshold)["accuracy"] == 1
