# Labeled evaluation and versioned quality policies

The benchmark command turns a shared CSV of human judgments into reproducible
measurements, per-domain thresholds, and a held-out error report. It runs locally;
images are not uploaded. It is an optional developer tool for comparing detector
changes. The browser checker, ordinary CLI, and API do not require labeled datasets.

## Try the whole workflow

From an installed checkout:

```bash
python examples/create_demo_dataset.py outputs/demo-dataset
laplacian-blur-benchmark outputs/demo-dataset/labels.csv --calibrate --output outputs/demo-run
```

This creates synthetic document and product images. Each domain has separate
calibration and test captures with both usable and retake labels. The demo verifies
the workflow; its results and thresholds are not evidence of real-world accuracy.
Use a fresh output directory on each run; existing reports are not overwritten.

## Prepare a real dataset

Create a UTF-8 CSV (a UTF-8 BOM is also accepted):

```csv
filename,label,split,group,domain,reason
documents/page-01.jpg,usable,calibration,scan-session-01,documents,
documents/page-02.jpg,retake,calibration,scan-session-02,documents,text_unreadable
documents/page-03.jpg,usable,test,scan-session-03,documents,
documents/page-04.jpg,retake,test,scan-session-04,documents,text_unreadable
```

| Column | Meaning |
| --- | --- |
| `filename` | Image path relative to the manifest directory or `--image-root` |
| `label` | Human judgment: `usable` or `retake` |
| `split` | `calibration` for threshold selection; `test` for held-out reporting |
| `group` | Globally unique capture/session/subject identifier for related images |
| `domain` | Use case, such as `documents`, `products`, or `vehicle-inspection` |
| `reason` | Optional reason for the human judgment |

Define what "usable" means for the task before labeling. It need not mean that the
only defect is blur: exposure or framing failures can reveal the limits of a blur
metric. Do not change human labels merely because the detector disagrees.

Group related captures, derived crops, recompressed copies, and near duplicates
together. A group must belong to one split across the entire manifest, including
different domains. The tool rejects duplicate paths, byte-identical files, and
groups shared across calibration and test. Byte hashes cannot identify visually
similar images saved with different encodings; grouping still requires care.

Calibration needs both labels for each domain. Every domain needs held-out test
samples. Test metrics for a missing class are `null`, not a perfect score. A tiny
test set remains weak evidence even when all its images are classified correctly.

Image paths must stay inside the chosen image root. Absolute paths, parent-directory
traversal, and symlinks escaping the root are rejected. Missing or unreadable images
fail the run rather than silently shrinking the evaluation denominator.

Record dataset source, permission/license, labeling instructions, reviewer decisions,
and unresolved disagreements alongside the manifest. Share real images only with
permission and keep private datasets out of Git. Generated content under `outputs/`
is ignored by Git; explicitly choose which sanitized evidence belongs in a PR.

## Three evaluation modes

```bash
# Compare the existing development threshold with human judgments.
laplacian-blur-benchmark data/labels.csv --threshold 100 --output outputs/baseline

# Select a threshold independently for each domain using calibration rows only.
laplacian-blur-benchmark data/labels.csv --calibrate --output outputs/calibrated

# Evaluate a frozen policy without selecting new thresholds.
laplacian-blur-benchmark data/new-labels.csv --policy outputs/calibrated/policy.json --output outputs/recheck
```

Use `--image-root path/to/images` when images are separate from the CSV. Frozen
policies reject unknown domains, incompatible metric/preprocessing versions, and
test images matching the policy's calibration groups or byte hashes. The original
manifest can be evaluated again: its calibration rows remain calibration rows.

### Objective and decision boundary

An image predicts `retake` when `score < threshold`; equality predicts `usable`,
matching the existing detector and API.

By default calibration minimizes:

```text
(false_reject_rate + missed_retake_rate) / 2
```

This weights the two classes equally instead of allowing a majority of usable
images to dominate accuracy. You can change the relative class-error weights:

```bash
laplacian-blur-benchmark data/labels.csv --calibrate --missed-retake-cost 3 --output outputs/strict
```

The weighted objective is `(reject_cost * false_reject_rate + missed_cost *
missed_retake_rate) / (reject_cost + missed_cost)`. Costs must be finite and
positive. They weight class error rates, not estimated financial loss per upload.
Ties prefer fewer missed retakes, then the lower threshold. Distinct score groups
move together during the sweep, so identical scores cannot be separated by labels.

Test labels never select thresholds. Repeatedly tuning design choices after
inspecting a test report can still overfit that test set; reserve a fresh final
evaluation set for consequential decisions.

## Report artifacts

| File | Contents |
| --- | --- |
| `policy.json` | Schema/metric versions, domain thresholds, calibration provenance, selection objective, runtime versions |
| `summary.json` | Per-domain, per-split confusion counts, error rates, retake precision/recall/F1, accuracy, balanced accuracy |
| `predictions.csv` | Every sample, label, split, score, threshold, prediction, outcome, and image SHA-256 |
| `errors.csv` | Held-out test mistakes only: `false_reject` or `missed_retake` |
| `thresholds.csv` | Calibration candidates and objectives; only emitted with `--calibrate` |

Retake is the positive class. False rejection means a usable image was rejected;
missed retake means an image requiring a retake was accepted. Rates and metrics
with a zero denominator are `null`. Compare per-domain test metrics rather than
pooling unlike use cases into one headline number.

The summary records manifest and canonical-policy SHA-256 fingerprints. Predictions
record hashes of the exact encoded bytes used for scoring. The policy records the
calibration groups/hashes, detector version, and raw native-resolution OpenCV
grayscale preprocessing contract. Identical policies have the same fingerprint
even when JSON formatting differs.

The report records current OpenCV/NumPy versions and `runtime_matches_policy`.
Runtime differences are visible rather than blocking reevaluation; numerical
equivalence across dependency versions is not guaranteed. Use the same dependency
versions when reproducing a result exactly. Policies are local evaluation artifacts;
the HTTP upload API does not consume them yet.

## What this does not establish

The algorithm still measures whole-image edge detail. Noise, low texture, lighting,
exposure, and subject location can cause errors. The benchmark enables measuring
these failures; calibration alone does not fix them. Local sharpness, exposure
checks, and new algorithms should be compared on appropriate labeled data before
they are adopted as quality gates.
