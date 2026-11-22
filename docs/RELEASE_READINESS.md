# Release readiness and review gates

This is an unreleased development candidate, not a production-readiness claim.
No release, PyPI publication, merge, main-branch push, or force push is authorized.

## Review chain (verified 2026-11-22)

| Review | Head | Base | Status |
| --- | --- | --- | --- |
| [Phase 2–3 PR #1](https://github.com/yyyunx/laplacian-blur-detector/pull/1) | `codex/sharpness-heatmap-benchmark` | `main` | Open draft, not merged |
| [Phase 4 PR #2](https://github.com/yyyunx/laplacian-blur-detector/pull/2) | `codex/image-quality-diagnostics` | `codex/sharpness-heatmap-benchmark` | Open draft, exactly three commits |

The Phase 4 diff contains only `1f0164c`, `7ef2b71`, and `4388749`. It preserves
the prior CLI/API/benchmark/heatmap contracts and adds opt-in diagnostic hints.
Its baseline validation was 209 Python tests, 21 frontend tests, builds and
installed-wheel smoke checks, plus seven successful CI jobs per milestone.

Phase 5 starts from `4388749` on `codex/release-readiness-hardening`. Keep this
review chain intact. After PR #1 is actually merged, inspect ancestry and the
Phase 4 diff before deciding whether to retarget PR #2 to main; do not retarget
or merge automatically. If the first PR is squash-merged, inherited commits may
need maintainer coordination rather than a blind base change.

Both PR descriptions explicitly distinguish numeric/controller tests from pending
desktop/mobile visual acceptance. No real-image accuracy improvement is claimed.

## Required gates before a formal release

- [x] Verify both draft PRs, intended bases and commit scope.
- [ ] Measure 1080p, 4K, 12MP and safely feasible 20MP latency/peak RSS, including
  two concurrent large analyses; record environment and safety stops.
- [ ] Check busy/error/cancellation/timeout recovery without freeing an active
  worker slot prematurely or allowing work to grow without bound.
- [ ] Complete real 1280px/390px browser visual acceptance, including EXIF,
  pointer/touch/keyboard, opacity, errors/retry and stale responses. A manual
  checklist is acceptable evidence of an open gate, not a passed gate.
- [ ] Verify installation/demo in a clean dependency environment, wheel and sdist,
  supported Python/OS CI matrix, and Docker build/live smoke checks.
- [ ] Finish release notes, contributor steps, integration examples and explicit
  operational limits. Review the package contents for credentials/private data.
- [ ] Maintainer reviews/approvals and merging in the correct order.
- [ ] Maintainer decides version/tag, supported environments and publication;
  none of those publishing actions are performed by this development task.

Until the resource, packaging and browser gates have evidence, formal release is
not recommended. Encoded-intensity/sharpness heuristics remain advisory and do
not establish complete photo quality or real-world accuracy.
