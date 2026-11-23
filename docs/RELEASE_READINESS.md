# Release readiness and review gates

This is an unreleased development candidate, not a production-readiness claim.
No release, PyPI publication, merge, main-branch push, or force push is authorized.

## Review chain (verified 2026-11-23)

| Review | Head | Base | Status |
| --- | --- | --- | --- |
| [Phase 2–3 PR #1](https://github.com/yyyunx/laplacian-blur-detector/pull/1) | `codex/sharpness-heatmap-benchmark` | `main` | Open draft, not merged |
| [Phase 4 PR #2](https://github.com/yyyunx/laplacian-blur-detector/pull/2) | `codex/image-quality-diagnostics` | `codex/sharpness-heatmap-benchmark` | Open draft, exactly three commits |
| [Readiness PR #3](https://github.com/yyyunx/laplacian-blur-detector/pull/3) | `feature/release-readiness` | `codex/image-quality-diagnostics` | Open draft, original six commits |
| [Build security PR #4](https://github.com/yyyunx/laplacian-blur-detector/pull/4) | `fix/container-build-toolchain` | `feature/release-readiness` | Open draft, two commits |
| [Runtime isolation PR #5](https://github.com/yyyunx/laplacian-blur-detector/pull/5) | `fix/container-runtime-isolation` | `fix/container-build-toolchain` | Open draft, runtime fix plus final handoff |

The Phase 4 diff contains only `1f0164c`, `7ef2b71`, and `4388749`. It preserves
the prior CLI/API/benchmark/heatmap contracts and adds opt-in diagnostic hints.
Its baseline validation was 209 Python tests, 21 frontend tests, builds and
installed-wheel smoke checks, plus seven successful CI jobs per milestone.

Phase 5 starts from `4388749` on `feature/release-readiness`. Keep this
review chain intact. After PR #1 is actually merged, inspect ancestry and the
Phase 4 diff before deciding whether to retarget PR #2 to main; do not retarget
or merge automatically. If the first PR is squash-merged, inherited commits may
need maintainer coordination rather than a blind base change.

The complete [integration plan](INTEGRATION_PLAN.md) records reviewed commit
ranges, CI, repository settings and the proposed Merge Commit sequence. No PR
base/head is retargeted by this task. No real-image accuracy improvement is claimed.

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

## Integration and acceptance gates

- [x] Review all five Draft PRs, bases/heads, linear ancestry and disjoint commit scope.
- [x] Measure 1080p, 4K, 12MP and safely feasible 20MP latency/peak RSS, including
  two concurrent large analyses; record environment and safety stops.
- [x] Check busy/error/cancellation/timeout recovery without freeing an active
  worker slot prematurely or allowing work to grow without bound.

- [x] **Maintainer Manual Browser QA Passed**, reported 2026-11-23 for EXIF rotation,
  heatmap, metric switching, opacity, hover, diagnostics, 390px layout, errors
  and batch flow. This is a maintainer report, not a Codex browser run.
- [ ] Maintainer decides whether to supplement missing browser/version/build,
  exact desktop width, screenshots, physical-touch/keyboard and individually
  unreported edge-case evidence; see [the scoped record](BROWSER_QA.md).
- [x] Provide a reproducible fallback [browser QA checklist](BROWSER_QA.md) and
  synthetic EXIF/display fixtures after the bounded Phase 5 binding attempt failed.
- [x] Verify installation/demo in separate clean wheel/sdist environments,
  including outside-checkout smoke and dependency consistency checks.
- [x] Require Python/OS, Node and container build/live HTTP gates in candidate CI;
  review the exact final SHA's result before publication, as described in
  [validation evidence](RELEASE_VALIDATION.md). Local Docker daemon is unavailable.
- [x] Finish release notes, contributor steps, integration examples and explicit
  operational limits. Review the package contents for credentials/private data.
- [x] Retain the completed 2026-11-22 package/container triage and remaining advisory
  limitations. Successful CI/report collection does not mean vulnerability-free.
- [ ] Maintainer reviews/approvals and merging in the correct order.

## Experimental pre-release gates (separate from merging)

- [ ] Maintainer accepts the remaining advisory risk for **trusted images in a
  bounded local environment only**. Public unauthenticated hosting/stable
  production use is not recommended.
- [ ] Choose/apply a true pre-release version/tag (proposal: `0.3.0a1`). Current
  metadata remains `0.3.0`; it is not a Python pre-release. Follow
  [pre-release preparation](PRERELEASE_PREPARATION.md).
- [ ] Build/check the final integrated/versioned artifacts, agree download assets,
  checksums and platform claims. Current local builds are review-only.
- [ ] Preserve security evidence before its 2026-12-06 artifact expiry, reassess
  at publication time, and accept the actual operator controls/monitoring ownership.
- [ ] Explicit authorization for tagging/publication. No merge, Release, tag or
  PyPI publishing is performed in this task.

Resource results and lifecycle scope are in [PERFORMANCE.md](PERFORMANCE.md).
Cancellation checks cover coroutine cancellation/client-style timeout, not actual
TCP/proxy disconnect behavior; no hard native-work deadline is implemented.

Maintainer-reported browser acceptance removes the earlier blanket "not accepted"
status for its scope. The stack has technical integration evidence; actual merge
approval remains with maintainers. Experimental publication additionally needs
version/artifact/risk decisions; production readiness is not claimed. Read the
[draft notes](RELEASE_NOTES.md), [integration examples](INTEGRATION.md) and
[security decision](../SECURITY-REVIEW.md). Encoded-intensity/sharpness heuristics
remain advisory, not complete photo quality or real-world accuracy evidence.
