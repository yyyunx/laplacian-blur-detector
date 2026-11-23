# 0.3.0a1 Experimental pre-release preparation

Python metadata is **0.3.0a1**, supplied dynamically by Hatch from
laplacian_blur_detector/__init__.py. It is a real Python pre-release suffix;
Development Status remains Alpha. This is a version Review PR, not a published
tag/Release/PyPI version. PR #1–#5 are [already merged](INTEGRATION_PLAN.md).

**Trusted images, bounded local environment only. Not Production Ready; public
unauthenticated HTTP hosting is not recommended. Container advisories remain.**

## Install the review source

```bash
git clone https://github.com/yyyunx/laplacian-blur-detector.git
cd laplacian-blur-detector
git switch --track origin/release/0.3.0a1
python -m venv .venv
# Activate using the platform-specific README instructions:
python -m pip install -e ".[server]"
python -c "import laplacian_blur_detector as p; print(p.__version__)"
laplacian-blur-demo --output outputs/alpha-demo
laplacian-blur-serve
```

Choose a new demo output directory on repeat. Serving defaults to loopback.
Use Docker's existing capability/no-new-privileges/read-only/resource controls
in [integration examples](INTEGRATION.md). No v0.3.0a1 tag or PyPI availability
is presumed by these instructions.

## Install a review attachment

Download the files supplied for this Review PR and verify SHA256SUMS against the
provided source manifest. These filenames are built from 0.3.0a1 source, not
renamed 0.3.0 archives. From the download directory, choose one in a clean venv:

```bash
python -m pip install "./laplacian_blur_detector-0.3.0a1-py3-none-any.whl[server]"
# Alternative in a separate clean venv:
python -m pip install "./laplacian_blur_detector-0.3.0a1.tar.gz[server]"
python -c "import importlib.metadata as m; import laplacian_blur_detector as p; assert m.version('laplacian-blur-detector') == p.__version__ == '0.3.0a1'"
```

Local Review files are under ignored outputs/prerelease-0.3.0a1/review-assets/:
wheel, sdist, RELEASE_NOTES.md, SOURCE.json and SHA256SUMS. SOURCE.json records
the exact committed source SHA/tree/version/build environment. Checksums cover
both packages, notes and source manifest; the checksum file excludes itself.
No asset is uploaded as a Release in this task, and no download URL is invented.

## Final assets after this version PR is merged

1. Fetch/verify final main and record its exact SHA/tree. Confirm the version PR
   merged without an unintended source change and its current main CI succeeds.
2. Build wheel/sdist from that SHA's clean archive. Recheck Hatch source,
   filenames, wheel METADATA, sdist PKG-INFO and installed version equality.
3. Run tests/check_distribution_contents.py with a generated-output sentinel
   present; inspect for credentials/private images/temp paths. Independently
   install wheel and sdist in clean venvs, run installed CLI/demo/API smoke outside
   checkout and pip check. Do not rename old 0.3.0 packages.
4. Rebuild notes, SOURCE.json and SHA256SUMS for the final main SHA. Review assets
   are not substituted for final publication assets, even if the source tree is
   unchanged by the merge. Reassess [security](PRERELEASE_SECURITY_REVIEW.md).
5. Maintainer approves risk/scope, exact assets and publication separately. Only
   then prepare a GitHub Draft Release; no tag/Release/PyPI action in this round.

## Compatibility and evidence limits

Python >=3.10; current CI covers Windows/Ubuntu 3.10/3.12/3.13 and Node 22,
with Linux/amd64 container evidence. macOS/ARM/every newer interpreter are not
certified. The py3-none-any wheel still needs supported NumPy/OpenCV binaries.
Core/CLI/API/default benchmark compatibility is retained; no algorithms or labels
change. Synthetic demo smoke is functional evidence, not a new accuracy experiment.

Maintainer Manual Browser QA Passed was reported 2026-11-23 for the listed
[scope](BROWSER_QA.md); Codex did not operate that browser. Browser/build/device,
physical touch, keyboard-specific evidence and screenshots were not supplied.
The historical Windows report rename error was not reproduced in bounded checks;
root cause remains unconfirmed. Keep this limitation visible if it recurs.
