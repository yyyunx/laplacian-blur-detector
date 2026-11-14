# Changelog

## Unreleased — 0.3.0

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
