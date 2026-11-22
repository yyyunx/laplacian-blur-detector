# Roadmap: a reusable image quality tool

The product is a general-purpose tool that people can use directly and developers
can integrate or improve through GitHub. Development collaboration means issues,
reviews, documentation, and code contributions. A shared labeling/review platform
is outside the current product direction.

## Implemented: open-source foundation

- Installable library and CLI, optional HTTP service, and bundled browser assets.
- Compatible checkout entry points, contribution guide, issue/PR templates, and CI.
- Optional developer benchmarking for comparing detector changes with human judgments.

Branch protection, private security reporting, and package publishing remain
maintainer operations. A committed configuration does not enable repository settings.

## Implemented: practical batch workflow

- Select or drop multiple files; inspect each preview and result.
- Track progress, cancel remaining requests, resume pending files, and retry failures.
- Filter by outcome, sort by score or name, and export the entire queue to CSV.
- Use the batch API with ordered per-file results and isolated file errors.
- Bound uploaded bytes, request streams, pre-decode dimensions, and analysis workers.

Users can start with their own images. No human labels or accounts are required.
Legacy decisions still use whole-image Laplacian sharpness. These changes improve
usability and resource handling, not established real-world classification accuracy.

## Implemented: core metrics and local visualization (Phases 1–2)

- NumPy/OpenCV-only Laplacian and Tenengrad core, with configurable local grids.
- Full-image derivatives before local statistics, avoiding synthetic grid borders.
- Independent bounded local HTTP analysis with EXIF-aligned coordinates.
- Relative Sharpness overlay, metric switch, opacity, hover/tap and keyboard inspection.
- Separate low-texture hatching without a local blur classification.
- Generated in-browser demo fixture and documented numeric/HTTP/controller tests.

Visual QA on real desktop/mobile browser viewports remains pending because the
browser automation tooling stopped during review; see [validation](VALIDATION.md).
Static illustrations are numeric outputs, not browser screenshots.

## Implemented: multi-metric experiments (Phase 3)

- Extend the existing benchmark with independently calibrated Laplacian/Tenengrad policies.
- Preserve default CLI/policy behavior, split isolation, fingerprints, and error reports.
- Compare held-out classification metrics and decode-plus-measurement latency in CSV/JSON/SVG.
- One-command reproducible six-condition synthetic dataset and demo artifacts.
- Versioned metric/preprocessing checks and per-reason failure summaries.

No real-image accuracy gain has been established. Local image-level aggregation
is deferred until evidence/texture rules and aggregation behavior are specified.

## Next: explain more image quality problems

- Phase 4 now measures mean/median brightness, dark/bright-channel ratios,
  resolution and existing sharpness, with configurable advisory hints in the core,
  independent API and existing image page. These are encoded-value proxies,
  not complete quality or sensor-clipping decisions.
- Complete real desktop/mobile visual acceptance for both the heatmap and quality
  panel; browser tooling remained unavailable during Phase 4 review.
- Validate task-specific diagnostic policies on representative labeled images.
- Keep sharpness results separate from other quality findings so API clients can
  choose which checks matter for documents, products, or another use case.
- Compare local sharpness and additional metrics on relevant samples before changing
  existing score semantics or rejection defaults.

Done when a caller can identify why an image needs attention and decide which
checks apply without needing a labeling workflow.

## Next: smoother operation and integration

- Measure latency and peak memory across supported resolutions and batch sizes.
- Add deployment-specific timeouts, rate limits, and access controls where needed.
- Improve dependency/release reproducibility and installation documentation.
- Add examples for backend upload pipelines, document capture, and product photos.
- Add a background-job interface only if real workloads outgrow bounded requests.

Done when another developer can install, integrate, debug, and update the tool
using documented contracts and reproducible checks.

## Optional contributor evaluation

[Benchmarking](BENCHMARKING.md) is available for contributors who want labeled
error reports, per-domain threshold calibration, and versioned policies. Synthetic
examples verify the workflow; they do not establish real-world accuracy. This is
an optional development aid, not a prerequisite or the main product flow.
