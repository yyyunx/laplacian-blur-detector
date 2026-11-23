# Ordered integration plan — awaiting maintainer confirmation

Reviewed 2026-11-23. **Instructions only: no merge, base retarget, Ready-for-review
transition, branch deletion, Release, tag or PyPI upload was performed.**
Five existing Draft PRs are retained. This final documentation/packaging follow-up
is appended to #5; its head SHA must be checked after the push.

## Verified stack and review findings

| PR | Base → Head | Runtime baseline head | Own work commits after this follow-up |
| --- | --- | --- | ---: |
| [#1](https://github.com/yyyunx/laplacian-blur-detector/pull/1) | main → codex/sharpness-heatmap-benchmark | fd2d00c | 5 |
| [#2](https://github.com/yyyunx/laplacian-blur-detector/pull/2) | codex/sharpness-heatmap-benchmark → codex/image-quality-diagnostics | 4388749 | 3 |
| [#3](https://github.com/yyyunx/laplacian-blur-detector/pull/3) | codex/image-quality-diagnostics → feature/release-readiness | 5b8a716 | 6 |
| [#4](https://github.com/yyyunx/laplacian-blur-detector/pull/4) | feature/release-readiness → fix/container-build-toolchain | 81b2219 | 2 |
| [#5](https://github.com/yyyunx/laplacian-blur-detector/pull/5) | fix/container-build-toolchain → fix/container-runtime-isolation | df1e564 + this follow-up | 2 |

Before this follow-up, all 17 source commits were disjoint and every PR base was
the preceding head/merge base, with no behind commits. This follow-up adds one
commit to #5, making 18 distinct work commits; it does not append to #3's six.
GitHub reported all five PRs mergeable/clean, with no submitted review objects.
That is technical eligibility, not maintainer approval or security certification.

Complete per-PR patches/commit ranges were reviewed. Legacy `blur_detector.py`,
`cli.py` and `server.py` have no diff from main. Existing blur API response fields,
default benchmark/calibration behavior and frozen-policy isolation are retained;
new metrics/endpoints are additive. Full-image derivatives and native integer
allocation changes preserve score definitions. Controllers use request-generation
checks and text-based rendering. Existing contract/numerical/controller checks
remain relevant; no benchmark labels or thresholds were changed for appearance.

One actual packaging issue was found: the current source build included 19
untracked files under `examples/outputs/browser-qa`. They are preserved locally,
excluded explicitly from sdist, and checked by a build sentinel plus archive
inspection. No user's images/outputs are added to the commit or download bundle.

Latest PR CI before this follow-up: #1 [7/7](https://github.com/yyyunx/laplacian-blur-detector/actions/runs/44991498274),
#2 [7/7](https://github.com/yyyunx/laplacian-blur-detector/actions/runs/44994331183),
#3 [8/8](https://github.com/yyyunx/laplacian-blur-detector/actions/runs/44998732974),
#4 [8/8](https://github.com/yyyunx/laplacian-blur-detector/actions/runs/45000702006),
#5 [8/8 at df1e564](https://github.com/yyyunx/laplacian-blur-detector/actions/runs/45007310727).
Use #5's new head/run for final sign-off; do not treat its prior run as testing the
new packaging exclusion. Current review evidence is attached to the Draft PRs.

## Why Merge Commit for this stack

Use GitHub **Create a merge commit**, preserving each reviewed commit SHA and the
parent relationships used by dependent PRs. After #1 is merged, its original head
is an ancestor of main; #2 can then be retargeted without replaying Phase 2–3 work.
Repeat this property through #5. Squash and GitHub Rebase-and-merge create new
SHAs: dependent heads retain the originals, so inherited commits/diffs can reappear.
This plan avoids rewriting review history to repair that situation.

Repository settings observed: Merge Commit is enabled; Squash and Rebase are also
enabled; automatic branch deletion is disabled. main is unprotected and no ruleset
was returned. Settings were read, not changed. Maintainers decide protection and
required reviews/checks. #1/#2 currently have seven CI jobs, so requiring the later
container check indiscriminately before their integration can leave them pending.

## Safe operation sequence (perform only after confirmation)

1. Confirm the intended local-only experimental scope, advisory disclosure and
   [maintainer QA acceptance/evidence](BROWSER_QA.md). Freeze unrelated main work
   during this short integration window if practical. Re-read all heads/CI/reviews
   and repository rules; the recorded SHA snapshot is not a future guarantee.
2. Mark **#1 only** Ready for review when its review is accepted. Check current
   tests and merge commit preview; merge #1 with **Create a merge commit**. Keep
   its branch, since #2 still refers to it as base.
3. Fetch main. Verify original #1 head `fd2d00c` is an ancestor of main. Inspect
   #2 before and after changing **only its base to main**. Its intended work is
   exactly the three Phase 4 commits, with no Phase 2–3 duplication. Confirm CI
   for the current combined state, review, mark Ready, then Merge Commit #2.
4. Verify `4388749` is now an ancestor of main. Retarget **#3** to main only after
   inspecting ancestry/diff; expect the original six Phase 5 work commits.
   Confirm checks/review and Merge Commit #3. Do not merge #3 into its old feature
   base just because GitHub allows it.
5. Verify `5b8a716` is an ancestor of main. Inspect/retarget **#4** to main; expect
   two installer/OS-security work commits. Accept its remaining-advisory policy,
   confirm checks/review and Merge Commit #4.
6. Verify `81b2219` is an ancestor of main. Inspect/retarget **#5** to main; expect
   the runtime-isolation commit plus this handoff/packaging commit. Confirm the
   new package-content checks and current CI, review and Merge Commit #5.
7. Verify all five reviewed heads are ancestors of main, inspect the cumulative
   diff and final tree, and check the resulting main CI. With no unrelated main
   changes, main's tracked tree should equal #5's reviewed final head tree.
   Integration merge commits are expected; duplicate/replayed work commits are not.
8. Only after the stack is accepted, decide version/tag and artifact publication
   separately using [pre-release preparation](PRERELEASE_PREPARATION.md). Retain
   legacy refs until no open PR uses them and preservation/deletion is approved.

Read-only checks for each stage (substitute the actual reviewed SHA):

```bash
git fetch origin
git merge-base --is-ancestor PREVIOUS_REVIEWED_HEAD origin/main
git log --oneline origin/main..origin/NEXT_HEAD_BRANCH
git diff --stat origin/main...origin/NEXT_HEAD_BRANCH
git diff origin/main...origin/NEXT_HEAD_BRANCH
```

Check content/check-run provenance after retargeting. Default pull_request workflow
events may not produce a new run solely for a base edit. Re-running an old Actions
run keeps its original SHA/ref and is not automatically new-base evidence. If
checks are invalidated or the combined tree changed, obtain fresh CI for that
state. With approval, GitHub **Update branch using Merge Commit** can merge the
new base into the next head and trigger synchronize CI without rewriting commits;
record that extra integration merge and recheck the intended work/tree. Do not
choose Update with Rebase or bypass a failed check.

If any ancestor test, expected diff or tree check fails, stop that stage. If a
predecessor was squash/rebase merged, coordinate a separate reviewed integration
branch from the new main with only the intended successor changes. Do not blindly
retarget, force-push/rebase the existing review heads, or delete active base refs.

## Maintainer decisions still required

- Approval to begin ordered merges and to mark Drafts Ready; accept/reject the
  reviewed changes. This task supplies no GitHub review approval on your behalf.
- Whether to configure main protections/required reviews and suitable CI checks.
- Acceptance of remaining native/container advisories for trusted local use;
  public unauthenticated hosting remains unsuitable. See [triage](CONTAINER_TRIAGE.md).
- Whether missing exact-browser/build/touch/keyboard evidence needs supplementing.
- Experimental version/tag, final assets/checksums, platforms and release timing.

Primary behavior references: [GitHub merge strategies](https://docs.github.com/en/pull-requests/reference/pull-request-merges),
[workflow reruns](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)
and [pull_request events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request).
