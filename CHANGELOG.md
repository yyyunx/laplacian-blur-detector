# Changelog

## Unreleased — 0.3.0

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
