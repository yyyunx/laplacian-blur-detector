# Completed stacked integration record

PR #1–#5 were merged with Merge Commits on 2026-11-23. Final integrated main:
`a91b8e5f0e5ffdc5baede93720a26f92144859a9`;
[main CI 8/8 success](https://github.com/yyyunx/laplacian-blur-detector/actions/runs/45095834084).
This is a completed record, not a request to merge those PRs again.

| PR | Original reviewed head | Work commits | Actual merge commit |
| --- | --- | ---: | --- |
| [#1](https://github.com/yyyunx/laplacian-blur-detector/pull/1) | fd2d00c | 5 | 471b6dde0dd5a7e1544cf86dfec20c60ffcb66d9 |
| [#2](https://github.com/yyyunx/laplacian-blur-detector/pull/2) | 4388749 | 3 | ee56da7fee4b7c24547b523e6b8660b719ff2ee4 |
| [#3](https://github.com/yyyunx/laplacian-blur-detector/pull/3) | 5b8a716 | 6 | 2ed9717edb7bbb0391cd27e8d0e2793dee479bcf |
| [#4](https://github.com/yyyunx/laplacian-blur-detector/pull/4) | 81b2219 | 2 | 44106acc2aeac85e111d98475b6b586058ceedd1 |
| [#5](https://github.com/yyyunx/laplacian-blur-detector/pull/5) | b1ad94a | 2 | a91b8e5f0e5ffdc5baede93720a26f92144859a9 |

All 18 original work commits are ancestors of integrated main. Its tree is
`840969a37155f0d89bbadddec74f5bc026da82a7`, identical to the reviewed b1ad94a tree.
There are five merge commits and no replayed/rewritten work commits. All original
branches, including legacy codex/ review references and canonical feature/
aliases, are retained; no branch deletion or main force-push occurred.

## Independent merge and test evidence

After each predecessor merged, its head ancestry was checked and the next PR was
retargeted to main. Exact work ranges/diffs were retained. Stale GitHub synthetic
preview parents were recorded; current refs and git merge-tree --write-tree
independently established conflict-free expected content. Actual GitHub merge
parents and trees were then verified. Fresh main CI passed at every stage.
No unnecessary head commit was created to refresh a preview.

A local Windows test once received WinError 5 while renaming a staged benchmark
report. The implementation/test were unchanged from #4. An authorized bounded
recheck ran the isolated test once (passed), then the full suite once (220 passed,
two deprecation warnings); Windows CI 3.10/3.12/3.13 each reported 220 passed.
The old failure was retained as **unreproduced, suspected environmental issue;
root cause unconfirmed**. No skip, arbitrary sleep or source fix was introduced.
This does not prove a particular external lock owner or permanent resolution.

## Current release work

The separate release/0.3.0a1 branch changes version/release documentation only.
Its Draft PR targets main and must be reviewed separately; no automatic merge,
tag, Release or PyPI publication. After approval/merge, rebuild final assets from
the resulting main SHA using [pre-release preparation](PRERELEASE_PREPARATION.md).
Maintainer browser acceptance remains [scoped](BROWSER_QA.md); remaining
[container risks](PRERELEASE_SECURITY_REVIEW.md) are not erased by integration.
