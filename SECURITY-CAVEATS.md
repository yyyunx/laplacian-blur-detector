# Deployment and release caveats

This candidate supports review and bounded trusted local demos. It is not approved
as an unauthenticated public production service or a formal release.

- Maintainer Manual Browser QA Passed was reported on 2026-11-23 for EXIF rotation,
  heatmap/metrics/opacity/hover, diagnostics, 390px layout, errors and batch flow.
  Browser/build provenance, screenshots, real touch and keyboard-specific coverage
  were not supplied. Codex did not operate the browser; see [acceptance](docs/BROWSER_QA.md).
- Client timeout/abort cannot kill accepted native work. Slots stay held until
  completion; multiple server processes multiply the two-slot limit.
- RGB8 synthetic measurements do not bound every codec, 16-bit PNG, EXIF transform,
  concurrent upload or allocator. Provision memory/temp-storage headroom.
- Authentication, TLS, rate/connection limits, proxy deadlines, process budgets,
  monitoring and incident ownership belong to the deployment operator.
- Dependency ranges are not a deployment lock. CI and `pip check` are not CVE
  scans. Final follow-up pip-audit found six unique installer advisories in pip
  25.0.1; local environments were repaired and the independent Docker bootstrap fix is
  merged in PR #4. Full-image Trivy artifacts and findings require maintainer review.
  CI report collection can succeed while reporting vulnerabilities; it is not a
  severity-based publication gate. Reports are retained for 14 days: preserve
  reviewed evidence before expiry and rescan before release.
- The first full-image scan on the installer-fix branch reported 1 Critical,
  66 High, 121 Medium, 115 Low and 9 Unknown package records (149 unique IDs).
  Available Debian updates are now applied before adding image libraries; inspect
  the latest artifact to assess the resulting counts. The Critical libxml2
  CVE-2026-6653 has no fixed trixie package according to Debian's tracker; do not
  mix unstable repositories or silently suppress it to obtain a clean report.
  Reachability/vendor triage and remaining upstream issues block public release.
- Encoded brightness/exposure/sharpness proxies cannot establish complete photo
  quality or real-world accuracy. Low texture is insufficient evidence.

Finding owners, evidence and rollback are in [SECURITY-REVIEW.md](SECURITY-REVIEW.md).
Use [the release checklist](docs/RELEASE_READINESS.md); do not hide pending gates.

Current 0.3.0a1 version-candidate status and the 2026-11-23 merged-main
artifact/official Debian recheck are in [scoped release review](docs/PRERELEASE_SECURITY_REVIEW.md).
Earlier counts above identify historical snapshots, not the latest candidate.
