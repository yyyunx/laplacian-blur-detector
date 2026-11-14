# Architecture and extension boundaries

## Current implementation

```text
Python caller ---------> laplacian_blur_detector.blur_detector
CLI -------------------> image_utils + blur_detector
Dataset evaluator -----> image_utils + blur_detector ---> local CSV
Labeled benchmark -----> manifest + evaluation ---------> policy + held-out reports
Browser demo ----------> FastAPI ----------------------> image_utils + blur_detector
```

`laplacian_blur_detector` is the public Python namespace. Importing it loads the
measurement core without requiring FastAPI or Uvicorn. `.[server]` adds the HTTP
interface and demo. The root `web/` directory is the editable source of the demo;
wheel builds place its assets inside the installed package.

The root `src/`, `api/main.py`, and `scripts/` modules are compatibility entry points
for existing checkout users. New integrations should use the installed package
or the documented HTTP API. Compatibility modules delegate to the package so there
is one implementation of the algorithm.

The current service is stateless. It has no shared workspace, database, identity
provider, annotation queue, or stored image history. Scores are Laplacian variance,
not calibrated confidence values. The default threshold is a development default.

`evaluation.py` provides image-independent confusion metrics and threshold
calibration. `benchmark.py` validates a labeled manifest, scores the exact bytes
whose hashes are recorded, calibrates a separate threshold for each domain, and
exports a frozen policy plus per-split reports. Test samples do not participate in
threshold selection. Existing reports are not overwritten. The HTTP API remains
a stateless single-threshold service; policy loading is currently CLI-only.

## Boundaries for future work

Keep four concerns separate:

1. **Measurement:** compute named metrics from explicitly preprocessed pixels.
2. **Quality policy:** choose domain-specific rules and thresholds, with immutable versions.
3. **Evaluation:** compare results with labeled datasets and report failure cases.
4. **Collaboration:** authorize people to manage datasets, labels, reviews, and policy changes.

A document-scanning policy and a product-photo policy may use the same measurement
while having different acceptance rules. Do not put vehicle, customer, or team
conditions into `calculate_blur_score`.

Before adding a second metric, propose its input types, preprocessing, score range,
direction, errors, runtime cost, and validation dataset. Introduce a shared detector
interface when those concrete needs are known; do not add a plugin framework solely
to wrap the existing single function.

## Proposed collaboration model (not implemented)

```text
Workspace -> Membership (role)
Workspace -> Project -> Dataset -> Image
Project -> QualityPolicyVersion
Image + QualityPolicyVersion -> AnalysisRun
Image -> Annotation -> ReviewDecision
Mutations -> AuditEvent
```

An analysis run should record detector version, policy version, preprocessing,
measurements, decision, and timing. Re-running analysis creates a new run; changing
a threshold must not silently rewrite old decisions.

Suggested initial roles are owner, contributor, and reviewer. Membership must be
checked server-side for every resource and download; identifiers alone are never
authorization. Define whether reviewers may approve their own labels before building
the review queue. Use a revision field for concurrent label updates and return a
conflict instead of silently overwriting another contributor's work.

Use a relational store for metadata and private object storage for images once
persistence is approved as part of the product design. Establish a workspace's
retention/deletion policy before accepting real images. Do not reuse public sample
assets as a storage mechanism for team uploads.
