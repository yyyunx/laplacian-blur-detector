# Browser acceptance — NOT YET ACCEPTED

On 2026-11-22, the Phase 5 browser inventory call (`cua.getState`, 15-second
execution budget) timed out and reset its kernel. No reliable browser surface was
obtained. Further binding attempts stopped. **None of the desktop/mobile visual
checks below has passed in Phase 5; no browser screenshot was produced.**
Earlier numeric EXIF tests and frontend controller tests are separate evidence,
not a substitute for layout, rendering or input acceptance.

## Reproducible setup

```bash
python -m pip install -e ".[server]"
python examples/create_browser_qa_fixtures.py --output outputs/browser-qa
laplacian-blur-serve
```

Open http://127.0.0.1:8000 in a real browser. Use **Try generated demo** to bypass
the native file picker. The generated local fixture directory adds odd-size,
portrait, flat/dark/white and EXIF 2–8 JPEGs, alongside Pillow-transposed PNG
references. They contain only owned synthetic pixels. Select a new output folder
on repeat; existing fixtures are not overwritten. In browser developer tools,
use responsive widths of 1280 and 390 CSS pixels, 100% zoom, and note the browser
version/device pixel ratio. Test a real touch device too if emulation is used.

## Acceptance checklist (repeat at both widths)

| Check | Required observation | Result |
| --- | --- | --- |
| Layout | Controls, diagnostics text/policy editor and image fit without horizontal page overflow; mobile controls remain usable | Pending |
| Original/Heatmap | Demo shows original and aligned SVG overlay; first/middle/last cells cover the image with no shift or stretched margins | Pending |
| Relative mapping | Both metrics update the legend/raw scores; label says Relative Sharpness, never blur localization or cross-image normalization | Pending |
| Opacity | Set 0/55/100 using pointer and keyboard; original remains visible at 0, regions align at each setting | Pending |
| Hover | Pointer over corners/center gives matching x/y/width/height, metric score and texture information | Pending |
| Keyboard | Tab to the overlay/controls, use documented arrow navigation; focus and cell information are visible without a mouse | Pending |
| Touch | Tap cells on phone; details persist/readable without hover; scrolling still works | Pending |
| Low texture | `flat.png` has separate hatching/insufficient evidence, no Blurry rejection; demo flat regions also distinct | Pending |
| Dimensions | Portrait and 1027×773 images retain aspect ratio, complete grid remainder coverage, correct displayed coordinates | Pending |
| EXIF | Each `exif-2.jpg`…`exif-8.jpg` preview matches its `reference-exif-N.png`; heatmap coordinates and quality dimensions follow displayed orientation | Pending |
| Diagnostics | `{}` gives measurements without enabled warning rules; loading example hints gives the demo resolution warning, limitations and suggestion | Pending |
| Policy errors | Invalid/duplicate JSON or wrong intensity scale gives readable errors; correcting it and retrying succeeds without old hints | Pending |
| API errors/retry | Stop the local server or use DevTools Offline, request analysis, observe error and cleared stale output; restore service/network and retry | Pending |
| Stale responses | With DevTools throttling, rapidly select different images and metrics, edit policy and clear selection; old maps/hints must never repaint the latest selection | Pending |
| Batch compatibility | Start/cancel/resume a batch and retry failed files; counters, threshold decisions and CSV remain independent of heatmap/diagnostic settings | Pending |

For a deterministic grid error, use an image under 128×128 with the default 8×8
grid; correct to a permitted smaller grid and retry. For busy behavior, use two
large active analyses and confirm a third request's 503 message is recoverable;
do this only with adequate memory headroom, following [resource guidance](PERFORMANCE.md).
Browser abort cannot stop already accepted native processing.

## Evidence to retain

Record commit SHA, browser/OS/version, viewport/device, fixture, each result and
any failure. Save actual 1280px/390px screenshots under `docs/images/qa/` only after
reviewing for private content; include EXIF overlay, low-texture view, diagnostics
and error recovery. Screenshots alone do not prove keyboard, touch or race safety.
Do not check pending boxes until these actions have actually been observed.
See [release gates](RELEASE_READINESS.md); visual acceptance remains a release gate.
