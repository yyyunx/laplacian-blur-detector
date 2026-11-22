"""Single-metric CLI and frozen preprocessing contracts."""

import csv
import json

import cv2
import numpy as np
import pytest

from laplacian_blur_detector import benchmark

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def manifest(tmp_path):
    rng = np.random.default_rng(123)
    rows = []
    for split in ('calibration', 'test'):
        for label in ('usable', 'retake'):
            image = rng.integers(0, 256, (64, 64), dtype=np.uint8)
            if label == 'retake':
                image = cv2.GaussianBlur(image, (15, 15), 0)
            filename = f'{split}-{label}.png'
            assert cv2.imwrite(str(tmp_path / filename), image)
            rows.append(dict(filename=filename, label=label, split=split, group=f'{split}-{label}', domain='synthetic'))
    path = tmp_path / 'labels.csv'
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=['filename', 'label', 'split', 'group', 'domain'])
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_tenengrad_can_be_inferred_from_policy_but_cannot_reuse_laplacian_default(manifest, tmp_path, capsys):
    assert benchmark.main([str(manifest), "--metric", "tenengrad", "--output", str(tmp_path / "bad")]) == 1
    assert "own explicit --threshold" in capsys.readouterr().err
    output = tmp_path / "tenengrad"
    assert benchmark.main([str(manifest), "--metric", "tenengrad", "--calibrate", "--output", str(output)]) == 0
    policy = output / "policy.json"
    assert benchmark.main([str(manifest), "--policy", str(policy), "--output", str(tmp_path / "inferred")]) == 0
    assert benchmark.main([str(manifest), "--metric", "laplacian", "--policy", str(policy), "--output", str(tmp_path / "mismatch")]) == 1
    assert not (tmp_path / "mismatch").exists()


@pytest.mark.parametrize("field,value", [("version", 2), ("preprocessing", "sobel5")])
def test_tenengrad_policy_rejects_incompatible_definition(manifest, tmp_path, field, value):
    output = tmp_path / "original"
    assert benchmark.main([str(manifest), "--metric", "tenengrad", "--calibrate", "--output", str(output)]) == 0
    policy = read_json(output / "policy.json")
    policy["metric"][field] = value
    path = tmp_path / "altered.json"
    path.write_text(json.dumps(policy), encoding="utf-8")
    assert benchmark.main([str(manifest), "--policy", str(path), "--output", str(tmp_path / "invalid")]) == 1
