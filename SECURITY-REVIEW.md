# Release-candidate security review

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
  compatibility evidence. A dedicated CVE/container vulnerability scan was
  **not run** in Phase 5 and remains a release gate.

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
- Evidence/reproduction: [browser acceptance](docs/BROWSER_QA.md) is Pending,
  dependency ranges are not frozen, and there is no dedicated CVE/image scan.
- Impact: builds/tests do not establish visual/input acceptance or absence of
  vulnerabilities. CI does not configure repository protections/approvals.
- Required fix: human QA, dependency/image scan at release time and maintainer
  review; explicitly record chosen versions and deployment monitoring ownership.
- Validation: tracked as incomplete, with no production-ready claim.
- Owner/target: release maintainer, before formal publication.

## Decision and rollback

**CONDITIONAL for trusted loopback development/demo; public production deployment
and formal release are not approved.** See [caveats](SECURITY-CAVEATS.md).
No persistent-format/database migration is introduced. To roll back a deployment,
build an independent artifact from known-good Phase 4 `4388749` with its matching
dependency environment, smoke-test health/contracts, then switch traffic. Do not
reset a contributor's checkout or force-push. Operators own error/503 rates,
latency, RSS, temp-disk monitoring and incident routes; no hosted monitoring is
supplied. No release/tag/publication is created by this development task.
