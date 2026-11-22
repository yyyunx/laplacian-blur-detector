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

Phase 5 starts from `4388749` on `feature/release-readiness`. Keep this
review chain intact. After PR #1 is actually merged, inspect ancestry and the
Phase 4 diff before deciding whether to retarget PR #2 to main; do not retarget
or merge automatically. If the first PR is squash-merged, inherited commits may
need maintainer coordination rather than a blind base change.

Both PR descriptions explicitly distinguish numeric/controller tests from pending
desktop/mobile visual acceptance. No real-image accuracy improvement is claimed.

## Safe branch naming migration

| Canonical branch | Preserved commit at migration | Legacy review ref |
| --- | --- | --- |
| `feature/sharpness-heatmap-benchmark` | `fd2d00c` | `codex/sharpness-heatmap-benchmark` (PR #1 head, PR #2 base) |
| `feature/image-quality-diagnostics` | `4388749` | `codex/image-quality-diagnostics` (PR #2 head) |
| `feature/release-readiness` | `095fcf5` | Phase 5 ref renamed natively; no PR used the old ref |

GitHub documents that renaming an open PR's head closes that PR. The first two
branches therefore use same-SHA copies; both existing PRs retain their original
head/base relationship and are not duplicated or closed. These two legacy refs
are deliberately retained, not deleted. The Phase 5 branch had no PR head and
was safely renamed through GitHub's native API, preserving its commit history.
New development uses only the canonical naming convention.
See [GitHub's branch rename behavior](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository/renaming-a-branch).

After PR #1 merges, a maintainer must inspect ancestry/diffs and both canonical
and legacy refs before retargeting PR #2 or deleting legacy refs. Do not assume
that same-SHA aliases automatically retarget PR heads or follow subsequent commits.

## Required gates before a formal release

- [x] Verify both draft PRs, intended bases and commit scope.
- [x] Measure 1080p, 4K, 12MP and safely feasible 20MP latency/peak RSS, including
  two concurrent large analyses; record environment and safety stops.
- [x] Check busy/error/cancellation/timeout recovery without freeing an active
  worker slot prematurely or allowing work to grow without bound.

- [ ] Complete real 1280px/390px browser visual acceptance, including EXIF,
  pointer/touch/keyboard, opacity, errors/retry and stale responses. A manual
  checklist is acceptable evidence of an open gate, not a passed gate.
- [x] Provide a reproducible fallback [browser QA checklist](BROWSER_QA.md) and
  synthetic EXIF/display fixtures after the bounded Phase 5 binding attempt failed.
- [x] Verify installation/demo in separate clean wheel/sdist environments,
  including outside-checkout smoke and dependency consistency checks.
- [x] Require Python/OS, Node and container build/live HTTP gates in candidate CI;
  review the exact final SHA's result before publication, as described in
  [validation evidence](RELEASE_VALIDATION.md). Local Docker daemon is unavailable.
- [x] Finish release notes, contributor steps, integration examples and explicit
  operational limits. Review the package contents for credentials/private data.
- [ ] Perform release-time dependency/container vulnerability review and record
  chosen versions/image plus deployment-specific controls/monitoring ownership.
- [ ] Maintainer reviews/approvals and merging in the correct order.
- [ ] Maintainer decides version/tag, supported environments and publication;
  none of those publishing actions are performed by this development task.

Resource results and lifecycle scope are in [PERFORMANCE.md](PERFORMANCE.md).
Cancellation checks cover coroutine cancellation/client-style timeout, not actual
TCP/proxy disconnect behavior; no hard native-work deadline is implemented.

Formal release is not recommended until browser acceptance, maintainer review,
release-time security checks and candidate CI are accepted. Read the
[draft notes](RELEASE_NOTES.md), [integration examples](INTEGRATION.md) and
[security decision](../SECURITY-REVIEW.md). Encoded-intensity/sharpness heuristics
remain advisory, not complete photo quality or real-world accuracy evidence.
