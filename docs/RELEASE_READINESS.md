# v0.3.0a1 release record and ongoing limits

[v0.3.0a1 Experimental Pre-release](https://github.com/yyyunx/laplacian-blur-detector/releases/tag/v0.3.0a1)
was published on 2026-11-23. PR #6 merged as
`5419d810e31395d5a36d659a8bfec3176e7ffccd`, also the tag's source commit.
This is a completed release record, not a pending publication gate or a
Production Ready claim. The documentation follow-up changes no published asset.

## Completed release evidence

- [x] PR #1–#5 integrated with all 18 original work commits preserved; PR #6
  version/documents merged using Merge Commit. All original branches retained.
  [Integration record](INTEGRATION_PLAN.md).
- [x] Version source, wheel/sdist metadata and installed library/API version agree
  on 0.3.0a1; no algorithm, label, threshold, CLI or API behavior change in the bump.
- [x] Final-main [CI 8/8 success](https://github.com/yyyunx/laplacian-blur-detector/actions/runs/45107557546).
  New final-main packages independently clean-installed; outside-checkout CLI,
  small functional Demo/API smoke, pip check and content/Sentinel checks passed.
- [x] Five attachments uploaded, downloaded and SHA256-verified before publishing;
  all five publicly downloaded without credentials and matched approved hashes.
  Source provenance/checksums are on the Release page.
- [x] Maintainer explicitly approved publication and accepted disclosed risks for
  trusted images in a bounded local environment. Pre-release marking retained.
- [x] Maintainer Manual Browser QA Passed was reported 2026-11-23 for EXIF rotation,
  heatmap, metrics, opacity, hover, diagnostics, 390px layout, errors and batch.
  It is maintainer-reported, not a Codex-operated browser test.

## Limits that publication does not resolve

- Missing exact browser/build/desktop width, screenshots, physical touch/keyboard
  and unreported subcase evidence remain explicit in [BROWSER_QA.md](BROWSER_QA.md).
- The historical Windows report-rename WinError 5 was not reproduced in bounded
  isolated/full and Windows CI checks; root cause is unconfirmed.
- Remaining native/container advisories, including libxml2, are disclosed in the
  [published security snapshot](PRERELEASE_SECURITY_REVIEW.md). No guaranteed
  image-path unreachability or universal malicious-input safety is claimed.
- Public unauthenticated HTTP/stable production use is not recommended. Native
  work survives client abort; processes multiply worker slots, and CLI/library
  calls do not inherit HTTP upload/pixel/worker guards.
- Operator memory/temp/network/monitoring responsibilities remain. Brightness,
  exposure and sharpness measurements are advisory, not complete photo quality
  judgments or evidence of improved real-world accuracy.

No repeated resource/Benchmark experiment or new browser acceptance is implied.
[Performance evidence](PERFORMANCE.md) and [historical validation](RELEASE_VALIDATION.md)
retain their original scopes. For future versions use the
[preparation procedure](PRERELEASE_PREPARATION.md); do not replace v0.3.0a1 assets.
