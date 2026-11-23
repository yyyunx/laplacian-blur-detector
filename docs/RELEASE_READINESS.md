# 0.3.0a1 release review gates

Experimental trusted-local-image candidate, not a production-readiness claim.
This round prepares a version Draft PR only: no merge, tag, GitHub Release,
PyPI publication, branch deletion or main push.

## Completed integration and existing evidence

- [x] PR #1–#5 merged using Merge Commit; 18 original work commits preserved.
  Integrated main a91b8e5 has the exact reviewed b1ad94a tree and
  [8/8 CI](https://github.com/yyyunx/laplacian-blur-detector/actions/runs/45095834084).
  [Merge SHAs and history](INTEGRATION_PLAN.md); all original branch refs retained.
- [x] Core/API/CLI/default benchmark compatibility, numerical, resource and
  controller checks; no algorithm/label changes for the version candidate.
- [x] 1080p–20MP and concurrent-resource evidence already recorded in
  [PERFORMANCE.md](PERFORMANCE.md); no repeat experiment needed for this bump.
- [x] Maintainer Manual Browser QA Passed, reported 2026-11-23 for EXIF rotation,
  heatmap, metrics, opacity, hover, diagnostics, 390px layout, errors and batch.
  This is maintainer-reported, not a Codex-operated browser test.
- [ ] Maintainer decides whether missing exact browser/build/desktop width,
  screenshots, physical touch/keyboard and unreported subcases need supplementing;
  [actual scope](BROWSER_QA.md) stays explicit.
- [x] Historical Windows report-rename failure retained as unreproduced after
  bounded isolated/full and Windows CI checks; root cause not claimed resolved.

## Version PR review gates

- [x] Apply 0.3.0a1 in Hatch's version source; update release/install documents.
- [ ] Review the exact version Commit/PR CI, fresh Python/frontend/Ruff results,
  new wheel/sdist metadata and content checks, clean independent installs,
  CLI/demo/API smoke, dependency audit and checksummed source provenance.
  Candidate evidence is supplied with the Draft PR and local Review attachments.
- [ ] Maintainer reviews and merges this version PR. Earlier PRs are complete;
  do not repeat their integration or delete their branches.

## Publication gates after version PR merge

- [ ] Accept remaining native/container advisory risk for **trusted images in a
  bounded local environment only**. No public unauthenticated HTTP/stable
  production claim. Read [current scoped review](PRERELEASE_SECURITY_REVIEW.md).
- [ ] Rebuild final wheel/sdist/notes/SOURCE.json/SHA256SUMS from the resulting
  exact main SHA; validate installed version 0.3.0a1 in separate clean venvs.
  Review attachments are not final publication attachments.
- [ ] Preserve finite-retention CI security evidence and reassess at publication;
  artifact expiry and exact DB/package versions are evidence limits.
- [ ] Explicitly approve exact assets, intended v0.3.0a1 tag, Experimental notice
  and eventual GitHub Draft Release. No tag or publishing authorized this round.

HTTP cancellation retains an active worker slot but does not kill native work.
CLI/library calls do not inherit HTTP limits. Memory/temp/network/incident controls
remain operator responsibilities; small-codec/fixture tests are not a proof of
universal leak freedom or malicious-input safety. Encoded quality measurements
remain advisory, not real-world accuracy evidence or a complete quality verdict.
See [pre-release procedure](PRERELEASE_PREPARATION.md), [notes](RELEASE_NOTES.md),
[security caveats](../SECURITY-CAVEATS.md) and [historical validation](RELEASE_VALIDATION.md).
