# Published 0.3.0a1 security snapshot — 2026-11-23

[v0.3.0a1 is published](https://github.com/yyyunx/laplacian-blur-detector/releases/tag/v0.3.0a1).
The maintainer approved the disclosed Experimental trusted-image bounded-local risk.
This is dated release evidence, not a new scan performed by the documentation PR.
**Not Production Ready; public unauthenticated HTTP hosting is not recommended.**
Publication does not approve stable production use or clear native advisories.

## Actual merged-image evidence

Final published-source main is 5419d810e31395d5a36d659a8bfec3176e7ffccd.
Its actual CI scan is run 45107557546, artifact 14787729323:
[full report/inventory/runtime probe](https://github.com/yyyunx/laplacian-blur-detector/actions/runs/45107557546/artifacts/14787729323).
ZIP SHA256: 5ff2fc9e94742ad1ff702549cbeda0e62610a0d4bfbf8ae30dfcb15401f3e210.
Reported 2026-11-23 03:43 UTC; CI retention expires 2026-12-07 03:43 UTC.
The published [SOURCE.json](https://github.com/yyyunx/laplacian-blur-detector/releases/download/v0.3.0a1/SOURCE.json)
retains the source/scan summary. Preserve full reports before expiry; recheck for
future releases instead of relabeling old data as a current scan.

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
work. No dependency/base change is introduced by this documentation PR.

Image-path reachability remains **not proven reachable**, not confirmed
unreachable and not a confirmed exploitation path. Existing benign XMP/loader
samples do not establish universal safety; refusing standalone XML is insufficient.
The dependency chain and other native/vendor/build-SBOM findings remain in
[CONTAINER_TRIAGE.md](CONTAINER_TRIAGE.md). No exhaustive new triage/fuzzing is
claimed. Malicious files can affect ordinary local native decoding as well as
remote HTTP use; trusted input and isolation limit exposure, not underlying bugs.

## Recorded published-package checks

Final-main wheel/sdist were built anew and installed in separate clean venvs;
CLI/demo/API/version smoke and pip check passed. pip-audit 2.10.1 checked 18 runtime
dependencies plus separately identified installer/validation pins, with no known
advisory records or skipped entries in that check. It does not cover OS/native
libraries, prove absence of vulnerabilities or constitute a source-code audit.
No new scan or dependency update is performed for the documentation follow-up.

Archive/Sentinel/private-path checks and Gitleaks 8.30.1 passed on the published
source/packages. They are not an exhaustive historical secrets audit. Generated
examples/outputs, caches, environments and private QA images were excluded.
Published packages/notes/source manifest/checksums are on the Release page and
remain unchanged; later repository documentation corrections do not replace them.

Remaining controls: no built-in HTTP auth/rate/connection limits, no hard native
deadline, multi-process slot multiplication and CLI/library lacking HTTP guards.
Retain loopback, resource/temp budgets and capability/no-new-privileges controls.
Current scoped [manual browser acceptance](BROWSER_QA.md) is independent of CVE
review and does not certify public deployment. Read [security caveats](../SECURITY-CAVEATS.md).
