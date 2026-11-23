# Draft experimental local-use pre-release notes — version not yet approved

Current source/package metadata: **0.3.0**, unreleased. Proposed experimental
version: **0.3.0a1**, awaiting maintainer decision and a reviewed version change.
These notes are not an announcement, tag or approved download release.

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

Python 3.10+; NumPy/OpenCV core, optional HTTP dependencies. Old API keys and default
Laplacian decisions are unchanged. Raw scores/thresholds are not interchangeable
across metrics, intensity scales or preprocessing. Local/diagnostic coordinates
follow EXIF display orientation; legacy blur preprocessing stays unchanged.

HTTP limits remain 10 MiB/file, 20MP/image, two active analyses/process, 32×32 cells
maximum and 16×16 pixel minimum cells. Client abort does not kill accepted native
work. Public-host operators must supply network controls and process budgets.

## Publication gates

Maintainer Manual Browser QA Passed was reported on 2026-11-23 for EXIF rotation,
heatmap/metric/opacity/hover, diagnostics, 390px layout, errors and batch flow.
Codex did not perform that browser session. Browser/build provenance, screenshots,
physical-touch and keyboard-specific evidence were not supplied; see [QA scope](BROWSER_QA.md).

The recorded 2026-11-22 container scan retains 1 Critical and 65 High package/
advisory records, plus other severities; this is not a count of independently
exploitable API bugs. libxml2 remains installed and its image-path reachability is
not proven, not universally ruled out. Installer and available OS fixes do not
resolve all vendor findings. Read [targeted triage](CONTAINER_TRIAGE.md).

Maintainer reviews/ordered merges, the final experimental version/tag, risk
acceptance, versioned wheel/sdist/checksums and publication approval remain open.
Follow [integration order](INTEGRATION_PLAN.md), [asset/version preparation](PRERELEASE_PREPARATION.md),
[release gates](RELEASE_READINESS.md) and [security caveats](../SECURITY-CAVEATS.md).
No GitHub Release or PyPI publication is performed by this work.
