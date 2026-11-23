# Published v0.3.0a1 downloads and future release preparation

[v0.3.0a1 Experimental Pre-release](https://github.com/yyyunx/laplacian-blur-detector/releases/tag/v0.3.0a1)
was published on 2026-11-23 after PR #6 merged. Its tag points to
`5419d810e31395d5a36d659a8bfec3176e7ffccd`. Package metadata is 0.3.0a1;
Hatch reads the version from laplacian_blur_detector/__init__.py.
This page no longer describes a pending version Review PR.

**Trusted images, bounded local environment only. Not Production Ready; public
unauthenticated HTTP hosting is not recommended. Container advisories remain.**

## Install the published package

Follow the [Windows PowerShell and Linux/macOS Wheel quick start](../README.md#five-minute-quick-start).
No clone is needed. [GitHub Releases](https://github.com/yyyunx/laplacian-blur-detector/releases/tag/v0.3.0a1)
contains the wheel, sdist, RELEASE_NOTES.md, SOURCE.json and SHA256SUMS. No PyPI
publication is implied. Download the Wheel and checksum file, compare the Wheel's
hash before installing, then use the venv's server command on loopback.

SOURCE.json identifies the exact published source SHA/tree/version/build tools;
SHA256SUMS covers both packages, notes and source manifest, excluding itself.
To run a whole-manifest checksum check, download all four listed files first.
The packages were rebuilt from final main after the version PR merged and
independently clean-installed/smoke-tested. Earlier local Review artifacts were
separate evidence. The published tag/assets are not rebuilt or replaced by
post-release documentation changes.

## Developer source installation

Use [source-checkout instructions](../README.md#developer-installation-source-checkout)
for contributions. Main contains ongoing changes; select tag v0.3.0a1 when you
need the published source exactly. Use a new demo output directory on repeat.
Docker examples retain loopback, no-new-privileges, zero capabilities, read-only
root and resource limits; see [integration](INTEGRATION.md).

## Future versions — not a request to republish v0.3.0a1

1. Review the new version/source change separately. Keep released tags/assets
   immutable; do not rename old archives or silently replace downloads.
2. Build future artifacts from the approved final source SHA and verify version
   source, filenames, wheel METADATA, sdist PKG-INFO and installed version equality.
3. Check distribution contents/Sentinel exclusions; install wheel and sdist in
   separate clean venvs, run outside-checkout CLI/demo/API smoke and pip check.
4. Generate new notes, SOURCE.json and SHA256SUMS for that exact source. Reassess
   security and preserve finite-retention evidence before publication.
5. Obtain explicit authorization for future merge/tag/Release/PyPI actions.
   This documentation PR creates no release, tag or package build.

## Compatibility and evidence limits

Python >=3.10; CI covers Windows/Ubuntu 3.10/3.12/3.13, Node 22 and Linux/amd64
containers. macOS instructions follow POSIX venv layout; macOS/ARM/every newer
interpreter are not certified by that matrix. The py3-none-any wheel still needs
compatible NumPy/OpenCV native binaries/system libraries.
Synthetic demo smoke is functional evidence, not an accuracy experiment.

Maintainer Manual Browser QA Passed was reported 2026-11-23 for the listed
[scope](BROWSER_QA.md); Codex did not operate that browser. Exact browser/build,
physical touch, keyboard-specific evidence and screenshots were not supplied.
The historical Windows report rename error was not reproduced in bounded checks;
root cause remains unconfirmed. [Published security snapshot](PRERELEASE_SECURITY_REVIEW.md)
retains native/container risks; a passing Python audit does not clear them.
