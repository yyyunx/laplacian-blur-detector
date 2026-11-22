# Draft release notes — 0.3.0 (unreleased)

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

This is a draft, not a published release. Actual browser visual/input acceptance,
maintainer reviews/ordered merges, vulnerability/image scan, version/tag decision
and publication approval remain open. Follow [release gates](RELEASE_READINESS.md),
[QA steps](BROWSER_QA.md) and [security caveats](../SECURITY-CAVEATS.md).
No GitHub Release or PyPI publication is performed by this work.
