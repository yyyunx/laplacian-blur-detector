# Phase 2 validation

Core/local HTTP/controller checks passed: 172 Python tests and 13 frontend tests.
Ruff, JavaScript syntax, source/wheel build, and installed-wheel smoke checks pass.
The original 66 tests and exact legacy blur endpoint response fields are retained.

Local derivatives are computed on the full image, then summarized per cell.
Tests cover grid-border ramps/real edges, low texture, complete remainder coverage,
EXIF transforms 2–8, upload/header/pixel/stream/grid limits, and shared resource recovery.
Controller tests cover opacity/inspection/toggles, error retry, stale images and
rapid metric changes, plus yielding local uploads to the batch workflow.

Browser visual QA is incomplete: the dashboard loaded, but file-chooser automation
stalled and later browser bindings failed. Native Chrome access was stopped by
Computer Use because the current URL could not be determined confidently. No real
browser screenshot or desktop/mobile layout/EXIF overlay verification is claimed.
The generated demo button avoids file-chooser dependence for subsequent manual QA.

Only Windows/Python 3.12 was executed locally. The configured CI matrix covers
Windows/Linux and Python 3.10/3.12/3.13. No real-image accuracy claim is made.
