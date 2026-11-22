# Phase 5 validation record (2026-11-22)

This records actual evidence and explicit limits, not publication approval.
Current acceptance update (2026-11-23): the maintainer reported manual browser QA
passed for the categories in [BROWSER_QA.md](BROWSER_QA.md). This is separate from
the historical automated checks below; Codex did not perform that browser session.
Phase 5 is based on `4388749`, with naming `5e34a61`, resources `0825628` and
manual-QA record `c12103a`. Use the corresponding pushed commit's Actions run
to identify the final candidate; no GitHub Release, tag or PyPI upload is created.

| Check | Observed result |
| --- | --- |
| Ruff | Passed |
| Python regression | 217 passed before readiness fix; three focused startup/deadline/contract regressions added; final suite is 220 |
| Frontend controller/mapping tests | 21 passed; no npm dependencies |
| Package build | sdist and wheel built successfully |
| Fresh wheel environment | Actual dependency installation, outside-checkout CLI/API/demo smoke and `pip check` passed |
| Fresh sdist environment | Isolated source build/install, outside-checkout CLI/API/demo smoke and `pip check` passed |
| Fresh dependency regression | 217 passed with NumPy 2.5.5, OpenCV 5.1.0.95, FastAPI 0.165.0, Pillow 13.0.0; one upstream httpx/TestClient deprecation warning |
| Live installed-wheel HTTP | Real loopback server outside checkout: assets, exact legacy keys/batch, both local metrics and diagnostic policy passed; server stopped afterward |
| Offline integration example | Expected explicit resolution warning produced |
| QA fixtures | Odd-size/portrait/flat/dark/white and EXIF 2–8/reference PNG generation completed |
| Resource experiment | All 16 size/mode cases completed up to 20MP; no guard stop/OOM; [details](PERFORMANCE.md) |
| Package content inspection | No virtual environments, output/temp directories, key files or bytecode; images were only generated demo assets |
| Existing candidate CI | Naming, resources and QA-record commits each passed seven jobs (Ubuntu/Windows × Python 3.10/3.12/3.13, plus Node) |
| New container gate | Added build, UID/read-only/resource-limited runtime and live HTTP smoke; the pushed candidate's Actions result is authoritative |
| First container CI attempt | Run 44997317964 built/started non-root successfully but smoke hit a startup connection reset; readiness now retries transient connection errors within its fixed deadline, preserving response assertions |
| Local Docker build | Not executed: Docker CLI 29.6.2 exists, Docker Desktop Linux daemon named pipe unavailable; CI provides the executable alternative |
| Manual browser QA update | Maintainer Manual Browser QA Passed, reported 2026-11-23; browser/build/screenshot/touch/keyboard evidence limits remain explicit |
| Automated browser operation | Earlier binding timed out; no Codex browser acceptance or screenshot is claimed |
| Dedicated CVE/container vulnerability scan | Completed in the 2026-11-22 follow-up; unresolved findings retained in [CONTAINER_TRIAGE.md](CONTAINER_TRIAGE.md), not a new scan today |

Fresh environments were created with `venv`, without `--system-site-packages`,
dependency `.pth` reuse or PYTHONPATH inheritance. Wheel and sdist used separate
environments and dependencies from PyPI (the second reused download cache, not
the first environment). Tests also ran in the existing development environment
with NumPy 2.5.3/OpenCV 5.0.0; resource numbers describe that environment only.
Existing upstream deprecation warnings are documented, not suppressed.

## Repeat distribution/runtime checks

```bash
python -m pip install -e ".[server,dev]"
python -m ruff check .
python -m pytest -q
node --test tests/web/*.test.mjs
python -m build
```

Use a new venv for each artifact. Install `dist/<wheel>.whl[server,dev]` or
`dist/<source>.tar.gz[server,dev]` with pip, then change to a directory outside
the checkout and run the absolute path to `tests/smoke_installed.py` using that
environment's Python. Run `python -m pip check`. For live HTTP/container checks,
follow [INTEGRATION.md](INTEGRATION.md); for Windows temp-directory restrictions,
pytest can use a new workspace-local `--basetemp=.pytest_tmp/<unique-name>`.
Never point pytest's disposable basetemp at valuable existing data.

CI now requires eight jobs: the six Python/OS combinations, Node checks and the
container gate. Each Python job installs/smokes both built wheel and sdist outside
checkout. Check the exact pushed SHA/branch, not merely an older successful run:
[candidate Actions](https://github.com/yyyunx/laplacian-blur-detector/actions?query=branch%3Afeature%2Frelease-readiness).

No benchmark label, threshold-selection rule or metric-version definition was
changed to improve reported results. Synthetic demo output verifies operation,
not real-world accuracy. Review [release gates](RELEASE_READINESS.md) and
[security caveats](../SECURITY-CAVEATS.md) before making a publication decision.
