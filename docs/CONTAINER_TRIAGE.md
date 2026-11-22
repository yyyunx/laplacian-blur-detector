# Targeted container security triage — 2026-11-22

Scope: PR #4 `81b2219`, Linux/amd64, its complete Trivy report and installed
Python inventory from Actions run 45000702006. Original artifact 14744839975 has
SHA256 `ab02fafb0830cbf3c29519ec0ab2bf40aa05561f210ae808661c3d2396bf0ca0`.
All findings remain visible. This is a bounded reachability review, not a claim
that every advisory is exploitable or that all native decoder paths are proven safe.
Acceptance update, 2026-11-23: [Maintainer Manual Browser QA Passed](BROWSER_QA.md)
is recorded for the reported scope. This does not change the 2026-11-22 security
snapshot or resolve its advisories; no fresh vulnerability scan is claimed here.

## Decision

- **Controlled local-use pre-release: conditionally reasonable**, after review of
  this hardening fix, for trusted/self-created images, a supported patched host,
  loopback-only access and the documented memory/PID/read-only/no-privilege bounds.
  Clearly retain the experimental label, outstanding advisories and the scope/
  evidence limits of maintainer browser acceptance. This is not publication approval or a stable release.
- **Public unauthenticated HTTP service: not recommended.** Untrusted native image
  decoding, uncertain XML/metadata reachability, no hard native-compute deadline
  and no per-client/connection limits remain. Put access control, request/rate
  limits, TLS, monitoring and isolation outside this toolkit if exposing it.
- The same caution applies locally when opening attacker-supplied/downloaded
  images. "Local" does not make a malicious file safe. Direct library/CLI calls
  also do not inherit the HTTP upload/pixel/worker limits.

## libxml2 CVE-2026-6653 — highest-priority unresolved parser question

Installed version: `2.12.7+dfsg+really2.9.14-2.1+deb13u3`, actual library
`/usr/lib/x86_64-linux-gnu/libxml2.so.2.9.14`. The version string does not establish
an upstream 2.12.7 fix: Debian reverted to a 2.9.14-based source.

The installed-package dependency graph is:

```text
libgl1 → libglx0 → libglx-mesa0 → mesa-libgallium → libllvm19 → libxml2
```

libllvm19 is the sole direct reverse dependency in the recorded image. This is
an OS graphics/LLVM dependency, not a Python application import or a build-only
finding. Keep its scanner record even if a sample does not load it.

[Debian's tracker](https://security-tracker.debian.org/tracker/CVE-2026-6653)
marks this trixie version vulnerable, with no fixed trixie package and minor/no-dsa
disposition. Its upstream fix concerns XML entity/parser handling and spans
several files; this project does not apply an unverified ad-hoc binary/source
patch. Do not mix sid/forky packages into stable or delete libraries/metadata just
to reduce the report. Await a supported Debian update/backport, or evaluate a
separately reviewed base/codec-dependency change with ABI/functional evidence.

The HTTP path is `validate_header` (Pillow JPEG/PNG header), OpenCV `imdecode`,
then numeric analysis. Local/quality routes also call Pillow `getexif` for display
orientation. PNG `getexif` can call `load()`: this review therefore includes actual
metadata/pixel decoding, not just extension checks. Image metadata can contain XML.
In the inspected Pillow 13.0.0 source, XMP orientation fallback uses a regex in
`Image.getexif`; the separate XML-parsing `Image.getxmp` is not called by project
code. OpenCV 5.1.0 JPEG/PNG decoder sources use libjpeg/libpng, not a project call
to libxml2. That source evidence alone does not rule out a transitive native path.

**Reachability status: NOT PROVEN REACHABLE.** No exploit path has been confirmed;
universal unreachability has not been confirmed either. Do not classify the CVE
as "confirmed unreachable" simply because raw XML uploads are rejected.

`scripts/inspect_container_runtime.py` makes the limited evidence reproducible:
three small, owned JPEG/PNG fixtures, including finite benign compressed/XMP DTD
metadata, exercise real legacy/local/quality HTTP routes and guarded local workers.
It records server/probe loaded libraries, loader diagnostics, ELF dependencies,
installed dpkg versions/dependencies, optional XML bindings and actual kernel
privilege controls. No exploit, entity amplification, external entity or outbound
network test is used. Inspect `runtime-reachability.json`/`runtime-loader.log` in
the candidate CI artifact for actual observations; no universal negative claim is
derived from sampling. The probe does not trace every native parser function.

## Prioritized Critical/High groups

| Priority / class | Actual preconditions and evidence | Disposition |
| --- | --- | --- |
| 1 — OS libxml2 parser/URI/XInclude and Expat metadata/graphics libraries | libxml2 enters via LLVM/Mesa; Expat via Mesa/GBM. Numeric processing does not intentionally parse XML, but both libraries can exist behind native dependencies. | Retain unresolved runtime questions; prioritize vendor updates and metadata-path review over unrelated build advisories. No reachable exploit has been demonstrated. |
| 2 — util-linux / ACL local privilege helpers | Mount/nsenter/post-hook or file-ownership operations are required; HTTP analysis never starts these helpers or accepts their arguments. Existing non-root USER alone did not explicitly prevent later setuid/file-capability gains. | Drop all capabilities and enforce no-new-privileges; keep read-only root, bounded tmpfs, no host/device/Docker-socket mounts or privileged mode. This contains prerequisites; it does not patch helper libraries. |
| Scoped non-applicability — libxml2 Python SAX bindings, CVE-2026-74860 | Requires the libxml2 Python bindings/SAX callbacks, not ordinary stdlib ElementTree. The recorded Python/OS inventories contain no python3-libxml2/lxml application dependency. | Confirm binding presence in the runtime artifact. Do not apply this finding to the numeric worker merely because the C library is installed; adding XML bindings changes the assessment. |
| Scoped non-applicability — OpenSSL QUIC stream leak | CVE-2026-124709 requires a QUIC server/handshake/stream handling. Documented service is Uvicorn HTTP over TCP; it has no QUIC implementation or UDP/HTTP3 configuration. | Not an invocation path in the documented service. Audit any separately added QUIC proxy/server independently. |
| Scoped non-applicability — SQLite FTS5/session | Findings require corrupted databases/SQL/session operations. No database is opened or queried by this stateless service; the package graph includes lastlog dependencies instead. | No corresponding HTTP operation; re-evaluate if a caller embeds the library in a database application. |
| Scoped non-applicability — systemd-homed / X11 / terminal / Perl archive tools | Requires a running homed service, malicious X server, terminal database or Perl archive execution. Analysis starts none of them and uses no GUI; do not inherit DISPLAY/host sockets into the service. | Check binary/environment observations and keep those prerequisites disabled. Package presence or shared source-package CVEs alone do not establish an image-upload exploit. |
| Metadata/build tooling — setuptools 70.3.0 | Trivy's three setuptools records originate in pip's embedded `bom.cdx.json`; installed distribution inventory contains no setuptools. Application image requests never run pip/PackageIndex. | Retain metadata and vendor triage; inspect executable vendor paths in the runtime artifact. Do not install a second setuptools or strip its SBOM to hide the findings. |
| Python runtime dependencies | The 18 actual application distributions were audited; no package-level known vulnerabilities were reported in that pinned inventory. | This is not a native-binary audit or a guarantee about other versions permitted by dependency ranges. |

The scoped non-applicability statements refer to required operations/components
in the documented service. They are not blanket "safe everywhere" verdicts for
those packages or for user applications that reuse the Python library.

## Fixed and outstanding

PR #4 already upgrades vulnerable pip bootstrap and applies 30 available OS
package/advisory fixes. This follow-up corrects README's all-interface Docker
publish example to loopback and uses explicit capability dropping/no-new-privileges
in both documented deployment and CI. These controls require actual run settings;
the Dockerfile cannot unilaterally enforce them for arbitrary operators.

No scanner ignore rule, severity filtering, mixed stable/unstable repository,
dependency swap, metric change or benchmark-label change is used. Original
advisories remain recorded. Save reviewed artifacts before their 14-day expiry.
Reassess after base/codec/Pillow/OpenCV changes, enabling GUI/XML/QUIC/database
features, removing sandbox controls, or admitting untrusted remote users.

PR #1–#4 bases/heads stay unchanged. The independent follow-up is based on PR #4;
maintainers should review it after that stack, checking ancestry before retargeting
anything. No merge, release or PyPI publication is performed by this review.

## Primary sources

- [Upstream libxml2 patch referenced by Debian](https://github.com/GNOME/libxml2/commit/463bbeeca1805b5c4828f50d0fefc4eebaf620df)
- [Pillow 13.0.0 Image.getexif/getxmp](https://github.com/python-pillow/Pillow/blob/13.0.0/src/PIL/Image.py)
- [OpenCV JPEG decoder](https://github.com/opencv/opencv/blob/5.1.0/modules/imgcodecs/src/grfmt_jpeg.cpp) and [PNG decoder](https://github.com/opencv/opencv/blob/5.1.0/modules/imgcodecs/src/grfmt_png.cpp)
- [Debian: Python-binding issue](https://security-tracker.debian.org/tracker/CVE-2026-74860), [QUIC](https://security-tracker.debian.org/tracker/CVE-2026-124709), [SQLite](https://security-tracker.debian.org/tracker/CVE-2026-119374), [systemd-homed](https://security-tracker.debian.org/tracker/CVE-2026-16742), [X11](https://security-tracker.debian.org/tracker/CVE-2026-88806)
- [Docker runtime controls](https://docs.docker.com/engine/containers/run/)
