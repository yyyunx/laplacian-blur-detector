# v0.3.0a1 — Experimental Pre-release

Published 2026-11-23: [GitHub Release](https://github.com/yyyunx/laplacian-blur-detector/releases/tag/v0.3.0a1).
PR #6 merged; tag v0.3.0a1 points to
`5419d810e31395d5a36d659a8bfec3176e7ffccd`. Python package version is 0.3.0a1.
The [published release-note attachment](https://github.com/yyyunx/laplacian-blur-detector/releases/download/v0.3.0a1/RELEASE_NOTES.md),
SOURCE.json and SHA256SUMS record the final source and checked downloads.
This repository document may receive clarifications; the original tag and
published attachments remain unchanged. No PyPI publication was performed.

**Intended use: trusted images in a bounded local environment only.** Keep the
experimental label and advisory/evidence limits. This is not Production Ready and
is not recommended for an unauthenticated public HTTP service.

The toolkit supports Laplacian/Tenengrad measurements, full-image derivatives with
local grid statistics, Relative Sharpness visualization and optional diagnostic
hints. Existing blur library, CLI, single/batch API responses and default benchmark
behavior remain compatible. No AI model, database or login system is introduced.

## User-visible changes

- Inspect regions with metric/opacity controls and texture information. Separate
  low-texture hatching is not a blur label or cross-image normalized score.
- Measure encoded brightness, dark/bright-channel ratios, resolution and both
  sharpness metrics. Application-owned opt-in policies generate improvement hints;
  defaults do not impose universal warning or acceptance/rejection thresholds.
- Run the synthetic demo for independent calibration and comparison CSV/JSON/SVG.
  Synthetic failures remain documented; no real-world accuracy gain is claimed.
- Reduce unnecessary full-image allocations without changing metric definitions.
  See [measured costs](PERFORMANCE.md) for 1080p–20MP and concurrent workers.
- Install bundled browser assets from wheels and use [integration examples](INTEGRATION.md).
  Container runs as a non-root user and gains a CI build/live-HTTP smoke job.

## Compatibility and operations

Python 3.10+; NumPy/OpenCV core, optional HTTP dependencies. Existing API response keys and default
Laplacian decisions are unchanged. Raw scores/thresholds are not interchangeable
across metrics, intensity scales or preprocessing. Local/diagnostic coordinates
follow EXIF display orientation; legacy blur preprocessing stays unchanged.

HTTP limits remain 10 MiB/file, 20MP/image, two active analyses/process, 32×32 cells
maximum and 16×16 pixel minimum cells. Client abort does not kill accepted native
work. Public-host operators must supply network controls and process budgets.

## Published acceptance and known limitations

Maintainer Manual Browser QA Passed was reported on 2026-11-23 for EXIF rotation,
heatmap/metric/opacity/hover, diagnostics, 390px layout, errors and batch flow.
Codex did not perform that browser session. Browser/build provenance, screenshots,
physical-touch and keyboard-specific evidence were not supplied; see [QA scope](BROWSER_QA.md).

The 2026-11-23 merged-main image report still contains 1 Critical and 65 High
records, plus other severities; these are not counts of proven API exploit paths.
libxml2 remains installed; reachability is not proven, not universally ruled out.
The release's 2026-11-23 tracker recheck recorded no supported trixie fix. Read the
[scoped security review](PRERELEASE_SECURITY_REVIEW.md) and retained
[targeted triage](CONTAINER_TRIAGE.md); remaining findings are not suppressed.

A historical Windows benchmark report-directory rename received WinError 5.
The relevant code/test were unchanged between PR #4/#5; bounded single/full tests
and Windows CI subsequently passed. It remains an unreproduced environmental
suspected issue with root cause unconfirmed, not a claimed permanent repair.

The maintainer approved the Experimental limited-use risk and publication.
All five published attachments were publicly downloaded and checksum-verified.
Use the [Wheel quick start](../README.md#five-minute-quick-start),
[release record](RELEASE_READINESS.md) and [security caveats](../SECURITY-CAVEATS.md).
Future versions require their own approval and validation; this documentation
change does not rebuild or replace v0.3.0a1 packages or change product behavior.
