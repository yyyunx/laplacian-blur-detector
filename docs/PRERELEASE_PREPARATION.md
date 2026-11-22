# Experimental local-use pre-release preparation

Scope: trusted images, a bounded local environment, loopback-only serving and
explicit advisory disclosure. No production-ready, vulnerability-free, real-world
accuracy-improvement or general public-hosting claim is made.

## Version decision — not applied by this task

`laplacian_blur_detector.__version__` is currently **0.3.0**, read dynamically by
Hatch/pyproject metadata. It has no pre-release suffix. Development Status is Alpha.
The draft changelog/notes use 0.3.0; there is no new release/tag from this task.

Recommend **0.3.0a1** for the first experimental distribution, subject to maintainer
confirmation. A GitHub "Pre-release" checkbox does not change Python package
metadata: do not rename a 0.3.0 wheel to a1 or claim pip sees it as a pre-release.
After approval, update the version source, changelog/notes and intended tag together
in a reviewed change, rebuild from the final integrated SHA and verify metadata.
See [Python version semantics](https://packaging.python.org/en/latest/specifications/version-specifiers/).

## Installation and compatibility

Current source-review candidate (all five PRs, no published version assumed):

```bash
git clone https://github.com/yyyunx/laplacian-blur-detector.git
cd laplacian-blur-detector
git switch --track origin/fix/container-runtime-isolation
python -m venv .venv
# Activate using your platform's command, then:
python -m pip install -e ".[server]"
laplacian-blur-demo --output outputs/local-review-demo
laplacian-blur-serve
```

Use a new demo output directory on repeat. Once the reviewed stack/version is
merged and a tag is explicitly approved/created, replace the review branch with
that exact tag/SHA in release instructions. No such tag is presumed to exist now.
Keep Docker on loopback with no-new-privileges, zero capabilities, read-only root,
bounded temporary storage/memory/PIDs as in [integration](INTEGRATION.md).

The package declares Python >=3.10. Existing CI covers Windows/Ubuntu with
3.10/3.12/3.13, plus Node 22 checks and Linux/amd64 container runtime evidence.
macOS, ARM and every later Python/browser version are not certified by that matrix.
The wheel is py3-none-any for this Python code; NumPy/OpenCV still require suitable
platform wheels/system libraries. Server dependencies remain optional.
Legacy library/CLI/blur API/default benchmark contracts remain unchanged.

## Review attachments versus publication assets

Review builds are produced locally under ignored `outputs/integration-review/`.
Their 0.3.0 filenames/metadata are **review-only**, not an approved pre-release or
immutable publication artifact. No attachments are uploaded or final download URLs
invented by this task. Local generated `examples/outputs` are excluded from sdist;
the existing files remain untouched. CI builds with a generated-output sentinel
and checks both archives so that exclusion is exercised rather than assumed.

After version/merge approval, prepare from the exact final source:

1. Build a wheel and sdist using the existing build tool; run
   `python tests/check_distribution_contents.py --dist FINAL_DIST_DIRECTORY`.
2. Check filename/METADATA/PKG-INFO/__version__ agreement and the approved suffix.
3. Install each final artifact in a clean environment, run the existing installed
   CLI/API/demo smoke from outside checkout and `pip check`. Reuse existing
   source-level test evidence unless a new change/failure justifies more tests;
   final versioned artifacts still need their own packaging smoke.
4. Prepare `.whl`, `.tar.gz`, `SHA256SUMS`, draft release notes and security caveats.
   Include source SHA, build environment and links/hashes for the reviewed runtime
   inventory/Trivy/QA evidence. Do not attach private images, local fixtures,
   temporary logs, virtual environments or large benchmark datasets.
5. Preserve reviewed security artifacts before 2026-12-06 expiry and reassess at
   release time. The existing 2026-11-22 findings are dated evidence, not a new
   vulnerability database query today. A Docker image publication/digest, if ever
   desired, is a separate maintainer decision; no registry image is published here.
6. Only after explicit approval select the experimental/pre-release release mode,
   approved tag and exact versioned files. No Release/PyPI publishing is authorized
   in this task.

## Required release notice

Experimental, trusted local images only. Malicious files remain a native-decoder
risk even offline. Library/CLI calls do not inherit HTTP resource limits. Client
abort cannot kill accepted native work. Remaining container OS/vendor/SBOM findings
are retained; libxml2 reachability is not proven, not universally ruled out.
Public unauthenticated HTTP hosting is not recommended.

Maintainer Manual Browser QA Passed was reported on 2026-11-23 for its listed scope.
Codex did not perform that browser session. Browser/build provenance, physical
touch, keyboard-specific evidence and screenshots were not supplied. Disclose
those limits without treating all unreported details as failed tests.
