# Release-candidate security review

Current 0.3.0a1 review status: PR #1–#5 are merged at a91b8e5; installer/OS
and runtime-isolation fixes are integrated. The dated Phase 5 evidence below is
historical. See [current scoped review](docs/PRERELEASE_SECURITY_REVIEW.md) for
actual artifact counts, Debian status and candidate audit boundaries.


Scope: Phase 5, based on Phase 4 `4388749`, resource change `0825628` and QA record
`c12103a`. The final Phase 5 Git commit/CI identifies the reviewed source. This is
not a penetration test, a security guarantee, or public-deployment approval.

## Boundaries and evidence

- Untrusted HTTP bytes cross multipart parsing, Pillow header checks, OpenCV
  decode, bounded workers and JSON responses. Core/CLI inputs are trusted local
  arrays/files without HTTP limits. Previews stay local until requested analysis.
  No persistent image/result database exists; multipart may spool temporarily.
- Tests cover stream/file/pixel/grid/policy limits, invalid content, strict JSON,
  busy/recovery, numeric EXIF alignment and exact legacy response keys. Lifecycle
  tests retain active native-worker slots on coroutine cancellation/timeouts.
  [Resource experiments](docs/PERFORMANCE.md) include concurrent large analyses
  and bounded repeated-failure recovery, not proof of universal leak freedom.
- Filenames are metadata/extension selection, not upload destinations. Analysis
  has no shell, SQL, template execution, webhook, AI agent, session/cookie or
  tenant database. Those controls are inapplicable, not proof of public-site auth.
- Default serving binds loopback; no wildcard CORS middleware is introduced.
  Container runs as UID 10001; examples use loopback, read-only root, memory/PID
  budgets and bounded writable temporary storage. Docker context uses an explicit
  source/asset allowlist to exclude unrelated workspace data.
- Staged files receive targeted credential/private-key pattern checks before
  push; fixtures are generated. This is not a historical secret audit.
- Clean installation, `pip check`, build/runtime and Windows/Linux CI are
  compatibility evidence. The final follow-up uses pip-audit 2.10.1 and Gitleaks
  8.30.1, with full-image Trivy 0.76.2 reports collected in CI. Read the actual
  findings/limitations in PR #3 and the dependent installer-fix PR; scanner
  execution success does not imply absence of vulnerabilities.

## SEC-004: Vulnerable pip bootstrap in build environments

- Severity/status: Moderate installer risk; source fix supplied, requires the
  corresponding Docker build/scan evidence before release.
- Evidence: pip-audit found 12 records (six unique Advisory IDs) in pip 25.0.1
  from the clean build environments; CI's Docker install log also reported that
  bootstrap version. The 18 application runtime dependencies had no reported
  known vulnerabilities, with Linux CI and Windows inventories exactly matching.
- Impact: affected installer paths can process malicious wheels/index URLs;
  this is distinct from unauthenticated image analysis. Some advisories depend
  on Python/archive behavior, so applicability is not identical for all six.
- Required fix: upgrade pip to audited 26.3 before processing project dependency
  archives. Docker pins the reviewed base digest; refresh that digest and pip
  version together with actual release-time image scans.
- Validation: three isolated local environments upgraded and passed `pip check`;
  pip-audit re-scan reported no known vulnerabilities. CI collects the actual
  final image (including added OS libraries), rather than treating a base-only
  scan as equivalent. Check its JSON artifact for findings and DB metadata.
- Owner/target: release maintainer, before publication. PR #3 remains the original
  six Phase 5 commits; the necessary fix is independently reviewable.

## SEC-005: Unresolved container distribution and SBOM findings

- Severity/status: Critical as reported by Trivy; open publication blocker.
- Evidence: first full-image report for `7223067`, Actions run 44999876825,
  contains 312 package/advisory records (149 unique IDs), including libxml2
  CVE-2026-6653. Debian's [tracker](https://security-tracker.debian.org/tracker/CVE-2026-6653)
  lists the installed trixie version as vulnerable, with no fixed trixie package;
  it also describes the issue as minor/no-dsa. Neither label alone establishes
  exploitability through this JPG/PNG API.
- Impact: inherited distribution components and embedded build SBOMs require
  vendor/reachability triage. Do not equate scanner records with independent
  exploitable application bugs or silently downgrade them.
- Required fix: apply available same-release OS updates, verify actual installed
  Python packages versus embedded SBOM components, and review remaining vendor
  findings before public deployment. Do not mix unstable repositories or add a
  vulnerable-component ignore rule solely to reduce counts.
- Validation: inspect the latest full-image JSON and installed-package artifact.
  Browser acceptance/evidence is separate from this finding; green report-collection CI
  does not constitute security approval.
- Owner/target: release maintainer with distribution/vendor support, before release.

## SEC-001: Public deployment requires operator controls

- Severity/status: Medium for the documented local demo; open deployment boundary.
- Evidence/reproduction: `server.py` defaults to 127.0.0.1; binding publicly
  exposes intentionally unauthenticated endpoints. See `SECURITY.md`.
- Impact: unauthorized consumption and host exhaustion without external controls.
- Required fix: operator-owned authentication where needed, TLS, rate/connection
  limits, deadlines, memory/CPU/temp-disk budgets and monitoring/incident routing.
  Do not add an unrelated login system to this library to make a readiness claim.
- Validation: deployment-specific tests pending.
- Owner/target: deployment maintainer, before public exposure.

## SEC-002: Abort is not a native-compute deadline

- Severity/status: Medium; mitigated by two slots/process, hard deadline open.
- Evidence/reproduction: cancel an instrumented local/quality coroutine after
  worker entry; replacement work receives 503 until the native worker exits.
- Impact: timed-out callers may leave bounded work running; premature slot
  release or unlimited retries would amplify resource use.
- Required fix: retain slot semantics and bounded retry guidance; process-isolated
  hard deadlines need a separate design if workloads justify them.
- Validation: coroutine cancellation/timeout recovery passes; actual TCP/proxy
  disconnect and long-duration codec leak tests not performed.
- Owner/target: operator before public deployment; maintainers if hard deadlines
  become a supported guarantee.

## SEC-003: Release evidence has open gates

- Severity/status: Low for local development; open release gate.
- Evidence/reproduction: [browser acceptance](docs/BROWSER_QA.md) is now
  maintainer-reported Passed for the listed scope (2026-11-23), with provenance and
  supplemental touch/keyboard evidence not supplied. Dependency ranges are not
  frozen, and final CVE/image findings still require
  release-maintainer review. The earlier Phase 5 baseline had no dedicated scan;
  final follow-up evidence is attached to PR #3 and the dependent fix PR.
- Impact: builds/tests do not establish visual/input acceptance or absence of
  vulnerabilities. CI does not configure repository protections/approvals.
- Required fix: human QA, dependency/image scan at release time and maintainer
  review; explicitly record chosen versions and deployment monitoring ownership.
- Validation: tracked as incomplete, with no production-ready claim.
- Owner/target: release maintainer, before formal publication.

## Decision and rollback

**BLOCKED for public production deployment/stable release due to unresolved
image findings and required maintainer risk/publication decisions.** Maintainer
manual browser acceptance is recorded for its reported scope. Trusted loopback development
can continue with the documented resource boundaries. See [caveats](SECURITY-CAVEATS.md).
The [targeted container triage](docs/CONTAINER_TRIAGE.md) distinguishes a
conditional trusted local-use experimental pre-release from public/stable hosting;
it does not declare libxml2 unreachable or authorize publication.
No persistent-format/database migration is introduced. To roll back a deployment,
build an independent artifact from known-good Phase 4 `4388749` with its matching
dependency environment, smoke-test health/contracts, then switch traffic. Do not
reset a contributor's checkout or force-push. Operators own error/503 rates,
latency, RSS, temp-disk monitoring and incident routes; no hosted monitoring is
supplied. No release/tag/publication is created by this development task.
