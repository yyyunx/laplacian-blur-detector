# Architecture and extension boundaries

## Current implementation

```text
Python caller ---------> blur_detector
Single-image CLI ------> image_utils + blur_detector
Dataset evaluator -----> image_utils + blur_detector ---> local CSV
Optional benchmark ----> manifest + evaluation ---------> local policy/reports
Browser batch queue ---> bounded single-image API ------> header check + blur_detector
Backend integration ---> bounded batch API -------------> ordered per-file results
```

`laplacian_blur_detector` is the public Python namespace. Importing it loads the
measurement core without FastAPI, Uvicorn, or Pillow. `.[server]` adds HTTP serving
and Pillow header inspection. The root `web/` directory is the editable source;
wheel builds bundle its assets, including the JavaScript module for CSV and sorting.

The root `src/`, `api/main.py`, and `scripts/` are compatibility entry points.
They delegate to the package so there is one implementation of the detector.

## Browser workflow

The browser maintains a local queue of file references and sends one image at a
time only after the user starts analysis. Results, failures, filters, and previews
live in browser memory. Cancellation aborts the current client request and stops
future requests; server work already accepted may still finish. Retrying failed
files preserves completed results. Threshold edits invalidate previous results.
CSV export includes the whole queue in the selected sort order, including pending
and failed rows. Clearing the queue or reloading clears local results.

## HTTP resource boundaries

Streaming middleware counts incoming request bytes before multipart parsing,
including requests without Content-Length. Oversized multipart parsing closes
opened upload files. Endpoints read at most the per-file limit plus one byte and
close all upload handles, including on errors.

Worker-thread analysis checks JPEG/PNG headers and dimensions with Pillow before
OpenCV decoding. A per-process bounded semaphore allows two active analyses;
additional work receives a retryable busy error instead of joining an unbounded
CPU queue. Batch API files are analyzed serially and returned in input order.
A file error is recorded for that file while other valid files continue.

The service does not persist images or results. Multipart uploads may spool to
local temporary files during a request; these are closed after the request. The
service does not add authentication, per-client rate limiting, or network timeouts.
See [SECURITY.md](../SECURITY.md) for deployment boundaries.

## Extension rules

- Keep measurement independent of HTTP, browser state, storage, and image domains.
- Add quality measurements without silently changing existing blur score semantics.
- Keep domain-specific acceptance rules outside the measurement core.
- Keep browser state and exports separate from server measurement logic.
- Document inputs, preprocessing, output scale, errors, and runtime cost for new metrics.

For example, document capture and product photography may use the same sharpness
metric with different acceptance rules. Do not add vehicle-specific conditions to
`calculate_blur_score`. Introduce a common metric/plugin interface when a second
concrete implementation needs it, rather than adding a framework around one function.

## Optional developer evaluation

`evaluation.py` implements image-independent confusion metrics and calibration.
`benchmark.py` validates manifests, records exact byte hashes, separates calibration
and test samples, and exports frozen policies. It is an optional contributor tool.
The HTTP API currently accepts a numeric threshold; it does not load policy files.
