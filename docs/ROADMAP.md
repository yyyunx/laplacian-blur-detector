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
The detector still measures whole-image sharpness only; these changes improve
usability and resource handling, not established real-world classification accuracy.

## Next: explain more image quality problems

- Add brightness, clipped exposure, and minimum-resolution measurements.
- Give specific suggestions based on detected problems rather than one generic rejection.
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
