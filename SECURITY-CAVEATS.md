# Deployment and release caveats

This candidate supports review and bounded trusted local demos. It is not approved
as an unauthenticated public production service or a formal release.

- Actual desktop/mobile visual and touch/keyboard acceptance remains pending;
  browser inventory timed out. No real screenshot is claimed.
- Client timeout/abort cannot kill accepted native work. Slots stay held until
  completion; multiple server processes multiply the two-slot limit.
- RGB8 synthetic measurements do not bound every codec, 16-bit PNG, EXIF transform,
  concurrent upload or allocator. Provision memory/temp-storage headroom.
- Authentication, TLS, rate/connection limits, proxy deadlines, process budgets,
  monitoring and incident ownership belong to the deployment operator.
- Dependency ranges are not a deployment lock. CI and `pip check` are not CVE
  scans. Final follow-up pip-audit found six unique installer advisories in pip
  25.0.1; local environments were repaired and a separate Docker bootstrap fix is
  supplied. Full-image Trivy artifacts and findings require maintainer review.
  CI report collection can succeed while reporting vulnerabilities; it is not a
  severity-based publication gate. Reports are retained for 14 days: preserve
  reviewed evidence before expiry and rescan before release.
- Encoded brightness/exposure/sharpness proxies cannot establish complete photo
  quality or real-world accuracy. Low texture is insufficient evidence.

Finding owners, evidence and rollback are in [SECURITY-REVIEW.md](SECURITY-REVIEW.md).
Use [the release checklist](docs/RELEASE_READINESS.md); do not hide pending gates.
