# Phase 2–3 development validation record

This historical record describes the Phase 2–3 baseline (`fd2d00c`). Phase 4
diagnostic checks and the current manual acceptance list are documented in
[DIAGNOSTICS.md](DIAGNOSTICS.md#phase-4-validation-and-manual-acceptance).
For the later 2026-11-23 Maintainer Manual Browser QA Passed report, use
[BROWSER_QA.md](BROWSER_QA.md); the historical automation limitation below is not
a claim that maintainer acceptance is still absent.

Review date: 2026-11-22 (Asia/Taipei). Development uses incremental commits on
`codex/sharpness-heatmap-benchmark`, with each tested milestone pushed and its
remote SHA/Actions checked before the next commit. Existing uncommitted Phase 1
work was retained and extended. No force push, merge, release, PyPI publication,
or hosted deployment is part of this work.

## Executed checks

| Check | Actual result |
| --- | --- |
| Full Python suite (`python -m pytest -q`) | 182 passed; two existing FastAPI/Starlette deprecation warnings |
| Ruff (`python -m ruff check .`) | Passed after correcting development lint errors |
| Frontend Node tests (`node --test tests/web/*.test.mjs`) | 13 passed, including the four original batch utility tests |
| JS syntax (`node --check web/app.js`, `node --check web/heatmap.js`) | Passed |
| Source/wheel build (`python -m build --no-isolation`) | Passed using installed build dependencies |
| Wheel installation and `tests/smoke_installed.py` outside checkout | Passed in a new venv, with existing dependency packages reused through a `.pth` file and no downloads |
| Installed new `laplacian-blur-demo` executable | Passed; generated dataset, maps, and comparison from outside checkout |
| Python 3.10 grammar parsing | Passed for all project Python files using `ast.parse(..., feature_version=(3, 10))` |
| Six-condition default synthetic demo | Executed; results recorded in [EXPERIMENTS.md](EXPERIMENTS.md) |
| Static generated heatmap illustrations | Opened and visually inspected; separate flat-content hatching present |

The initial new-venv smoke attempt under the sandbox's special temporary path
installed/imported successfully but its Windows console launcher exited with
status 1. Repeating in an ordinary workspace path under ignored `.pytest_tmp/`
resolved the launcher failure; CLI/API/assets/benchmark and the new demo then
passed from a working directory outside the checkout. The project tests were
not skipped or weakened to work around this environment issue.

## What the tests establish

- Original 66 tests still pass, including legacy Python imports, detector
  threshold/equality behavior, CLI output, upload API, batch workflow, and frozen
  benchmark policies. Exact successful response key sets for both old blur
  endpoints are additionally checked. Benchmark predictions CSV columns remain
  unchanged; timing uses a separate artifact and additive summary metadata.
- Full-image response cells preserve real edges across grid lines, avoid
  artificial reflection gradients on interior ramps, and cover non-divisible
  dimensions exactly once. Whole-image Laplacian scores retain legacy semantics.
- Local endpoint tests cover both metrics, default/max grids, minimum cell size,
  finite settings, invalid/empty images, encoded bytes/pixel/header/request-stream
  limits, shared busy slots, retry hints, and resource recovery after failures.
- EXIF rotations/mirrors 2–8 are numerically compared to an independent Pillow
  orientation reference. Coordinate alignment has **not** been visually verified
  in a real browser.
- Pure mapping/controller tests cover relative range exclusions, equal/all-low
  texture cases, opacity, hover/keyboard descriptions, Original/Heatmap switching,
  retry, image changes, rapid metric switches, stale completion suppression, and
  local requests yielding to batch work. These use a minimal DOM, not a layout engine.
- Both metrics have independent thresholds and frozen descriptors. Replay keeps
  classifications/policy fingerprints stable. Changing test labels cannot affect
  calibration. Unknown versions/preprocessing and explicit metric mismatches fail.
  Incomplete comparisons are not published as complete report directories.
- Seeded generation produces identical bytes/manifests within this dependency
  environment; capture variants stay together in one split. No numerical test
  requires the synthetic data to appear accurate.

## Browser and platform limits — not passed

The local dashboard loaded in the in-app browser. The native file chooser then
stalled, and subsequent browser bindings timed out/reset. A generated demo button
was added to remove file-chooser dependence. A later Windows native Chrome attempt
was stopped by Computer Use because it could not determine the current browser
URL confidently. Browser operations were stopped at that point.

Consequently the following remain **not executed to completion**:

- Desktop/mobile browser screenshot and responsive layout QA.
- Actual pointer hover, opacity, rapid switching, and SVG/image fitting in a live
  browser; automated controller tests passed, but do not prove rendered layout.
- Visual EXIF overlay alignment and mixed portrait/landscape preview inspection.

No real browser demo screenshot was captured. The PNGs under `docs/images/` are
numeric renderings, not substitutes for browser screenshots. The CSS includes
mobile wrapping rules, but they have not been validated on a real mobile viewport.
The browser fixture now permits these checks without opening a file dialog.

Local execution used Windows / Python 3.12.14. The Phase 2 Actions run
[44981889488](https://github.com/yyyunx/laplacian-blur-detector/actions/runs/44981889488)
passed all seven jobs: frontend utilities and Windows/Ubuntu with Python
3.10/3.12/3.13, including builds and installed-wheel smoke checks. Subsequent
milestone Actions are checked individually and reported at completion; grammar
parsing alone is not runtime validation. Local wheel checks reused dependencies
without downloads; GitHub Actions installs dependencies in its runner environments.

There is no human-labeled real-image dataset, accuracy validation, peak-memory
profile at the 20-megapixel limit, repeated timing protocol, or production load
test. Whole-image derivative arrays can consume substantial memory; the local
route retains the existing two-worker bound but has not been capacity-tuned.

## Supplemental visual checks (see maintainer-reported acceptance scope)

1. Run `laplacian-blur-serve`, open `http://127.0.0.1:8000`, and select
   **Try generated demo**. Set 8 rows and 12 columns, then select **Heatmap**.
2. Switch both metrics; change opacity from 0 to 100; hover/tap the left, middle,
   and right panels. The flat panel must be hatched and described as insufficient
   evidence, without a local blurry label. Inspect with keyboard arrow keys too.
3. Rapidly switch images/metrics and clear/remove the selected image while local
   work is pending. No old map should paint the new image. Run/cancel/retry a batch
   and confirm local settings never change its counts, threshold, or CSV.
4. Check landscape, portrait, odd dimensions and EXIF rotations/mirrors. Verify
   SVG rectangles align with the displayed image rather than letterbox margins.
5. Check 1280px and 390px widths, keyboard focus, no horizontal control overflow,
   and minimum-grid error recovery. Save actual screenshots only after observing
   the live results.

## Changed source groups

- Core: `laplacian_blur_detector/sharpness.py`, `__init__.py`.
- Service: `laplacian_blur_detector/api.py`, `config.py`.
- Benchmark/demo: `laplacian_blur_detector/benchmark.py`, `benchmark_comparison.py`,
  `synthetic.py`, `demo.py`, `examples/create_sharpness_demo.py`.
- Frontend: `web/app.js`, `heatmap.js`, `index.html`, `styles.css`, `package.json`,
  and the small generated `web/demo.png` fixture.
- Tests: `tests/test_sharpness.py`, `test_local_api.py`, `test_metric_benchmark_core.py`,
  `test_synthetic.py`, `test_metric_benchmark.py`, `test_demo.py`,
  `tests/web/heatmap.test.mjs`, `tests/smoke_installed.py`.
- Packaging/CI: `pyproject.toml`, `.github/workflows/tests.yml`.
- Docs: `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`,
  `THIRD_PARTY_NOTICES.md`, `docs/API.md`,
  `ARCHITECTURE.md`, `BENCHMARKING.md`, `ROADMAP.md`, `EXPERIMENTS.md`, this record,
  and four small curated files under `docs/images/`.

No dependencies or AI models were added. Synthetic datasets, full benchmark
reports, build artifacts, virtual environments, and temporary files remain in
ignored output/build/test directories.

## Phase 5 acceptance update

The bounded 2026-11-22 browser inventory attempt timed out before obtaining a
surface. Browser acceptance had not been completed at that point. Follow the consolidated
[desktop/mobile checklist](BROWSER_QA.md); generated fixtures and EXIF display
references can be created without any private images. No screenshot is claimed.

On 2026-11-23 the maintainer subsequently reported manual browser QA passed for
the listed feature categories; missing provenance and supplemental coverage are
explicit in [BROWSER_QA.md](BROWSER_QA.md). Codex did not perform that browser session.
