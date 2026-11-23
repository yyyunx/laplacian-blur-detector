# Scoped 0.3.0a1 security review — 2026-11-23

Version/documentation preparation only; no new dependency or Docker change.
Experimental trusted-image bounded local use. **Not Production Ready; public
unauthenticated HTTP hosting is not recommended.** Maintainer risk acceptance
and publication approval remain separate gates.

## Actual merged-image evidence

Read and SHA256-verified the existing merged-main CI artifact, not a new local
Docker scan: main a91b8e5, run 45095834084, artifact 14782344756.
[Full report/inventory/runtime probe](https://github.com/yyyunx/laplacian-blur-detector/actions/runs/45095834084/artifacts/14782344756).
ZIP SHA256: 3da12332e1d5b7477476cbfc4c1fc4e1432564e7c3e9bd31a59d224b89e01f50.
Reported 2026-11-23 01:41 UTC; expires 2026-12-07 01:41 UTC. Preserve prior
reports too; older evidence expires earlier. The version PR's normal CI will
build and collect another full-image report; read its exact source/DB metadata.

This snapshot has **1 Critical, 65 High, 94 Medium, 113 Low, 17 Unknown** records,
141 unique Advisory IDs. Counts are scanner records, not independent confirmed
HTTP exploit paths. Earlier dated counts are retained as history, not current
cleanliness claims. Unknown advisories are not silently treated as inapplicable.
Runtime probe still records UID 10001, NoNewPrivs=1 and zero effective/permitted/
bounding capabilities. Those controls reduce impact; they do not patch codecs.

## libxml2 and native input risks

Installed libxml2 remains 2.12.7+dfsg+really2.9.14-2.1+deb13u3;
CVE-2026-6653 has no fixed version in this image report. On 2026-11-23 the
[Debian tracker](https://security-tracker.debian.org/tracker/CVE-2026-6653) still
lists trixie affected/no-dsa and a fix in newer distributions, not a supported
fixed trixie package. Do not mix stable/unstable packages or hide the advisory.
Await a supported vendor update/backport or separately reviewed dependency/base
work. No such change is slipped into this version PR.

Image-path reachability remains **not proven reachable**, not confirmed
unreachable and not a confirmed exploitation path. Existing benign XMP/loader
samples do not establish universal safety; refusing standalone XML is insufficient.
The dependency chain and other native/vendor/build-SBOM findings remain in
[CONTAINER_TRIAGE.md](CONTAINER_TRIAGE.md). No exhaustive new triage/fuzzing is
claimed. Malicious files can affect ordinary local native decoding as well as
remote HTTP use; trusted input and isolation limit exposure, not underlying bugs.

## Candidate Python/package checks

New wheel/sdist clean installs will supply exact installed inventories, pip check,
and a bounded pip-audit check with database/tool details in the candidate's Review
evidence. That audit cannot cover OS libraries or prove absence of vulnerabilities;
no result is implied before execution. Build tools/test-only packages are recorded
separately from the project's runtime dependencies. No unnecessary project
dependency is added. Inspect the actual candidate audit and CI evidence for review.

Archive/path checks and targeted private-key/credential checks are performed on
candidate contents. They do not constitute an exhaustive historical secrets audit.
Generated examples/outputs, caches, virtual environments and local QA images must
not ship. Current review attachments are built from committed source, not the
working directory's unrelated files.

Remaining controls: no built-in HTTP auth/rate/connection limits, no hard native
deadline, multi-process slot multiplication and CLI/library lacking HTTP guards.
Retain loopback, resource/temp budgets and capability/no-new-privileges controls.
Current scoped [manual browser acceptance](BROWSER_QA.md) is independent of CVE
review and does not certify public deployment. Read [security caveats](../SECURITY-CAVEATS.md).
