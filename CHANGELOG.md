# Changelog

## Unreleased — 0.3.0

- Add versioned seeded synthetic sharp, Gaussian/motion/partial blur, flat-content,
  and noisy-blur experiments, recording parameters and split-isolated capture groups.
  Synthetic labels are generation conventions, not real-image accuracy evidence.

- Add single-metric Tenengrad benchmarking with independent calibration, strict
  frozen metric/preprocessing contracts, and separate decode/metric latency.
  Preserve default Laplacian policies, CLI usage, and prediction columns.

- Add an interactive Relative Sharpness overlay with Original/Heatmap toggle,
  Laplacian/Tenengrad selection, grid/texture controls, opacity, hover/tap details,
  keyboard inspection, and separate low-texture hatching. Colors are relative to
  the current image, not calibrated blur labels or cross-image scores.
- Add `/api/sharpness/local`, sharing upload/decode/request/pixel limits and
  analysis slots, with browser-aligned EXIF orientation, a 32×32 grid cap, and
  minimum 16×16 pixel cells. Retain exact legacy blur endpoint response fields.
- Correct unreleased local scoring to compute derivatives on the full image
  before per-cell statistics, avoiding artificial grid-edge reflections and
  preserving real cross-cell edges. Local scores near grid lines can change;
  public signatures, result fields, whole-image metrics, and benchmark stay compatible.
- Add numerical boundary, API/resource, mapping/controller tests and a synthetic
  local demo generator; bundle the heatmap module in installed wheels.
- Add NumPy/OpenCV-only core sharpness APIs: Tenengrad (mean squared 3×3 Sobel
  gradient magnitude), a Laplacian/Tenengrad selector, and configurable local
  grid analysis (default 8×8) with coordinates and complete remainder coverage.
- Report local grayscale standard deviation and configurable low-texture flags
  without treating low sharpness scores as blur decisions. Document metric
  definitions, intensity scales, crop effects, and non-comparable score ranges
  in the README and new Python API reference.
- Add synthetic unit coverage for metric formulas, Gaussian/local blur, flat and
  low-contrast content, invalid/empty inputs, non-divisible grids, and core-only
  imports. Preserve existing detector, CLI, HTTP, Web UI, and benchmark behavior.
- Add browser batch selection, progress/cancellation, failed-file retries,
  filtering, sorting, and CSV export without requiring labels or accounts.
- Add a batch API with per-file outcomes and public configuration endpoint.
- Bound encoded uploads, request streams, image dimensions before OpenCV decode,
  and active analysis workers; return actionable error codes and busy hints.
- Refocus the roadmap on a reusable tool and open-source development.
- Add labeled dataset benchmarking with independent calibration/test splits,
  per-domain threshold selection, configurable class-error weights, frozen quality
  policies, held-out confusion metrics, and CSV error lists.
- Record metric/preprocessing versions, runtime versions, and dataset/policy hashes;
  reject overlapping capture groups, duplicate bytes, and reused calibration data.
- Preserve previous reports and add a runnable synthetic document/product example.
- Reposition the project as a domain-independent image quality foundation.
- Add the installable `laplacian_blur_detector` package and optional server dependencies.
- Add `laplacian-blur`, `laplacian-blur-evaluate`, and `laplacian-blur-serve` commands.
- Bundle browser assets in the wheel; preserve checkout API and script entry points.
- Add contribution guidance, issue/PR templates, architecture and collaboration roadmap.
- Add lint, tests, builds, and installed-package smoke checks in CI.
- Dataset CLI default output is now `outputs/blur_scores.csv` relative to the
  working directory. Pass `--output` to choose an explicit location.

The blur score calculation, default threshold, and existing HTTP response fields
are unchanged. Team accounts, shared image storage, and review queues are not yet implemented.
