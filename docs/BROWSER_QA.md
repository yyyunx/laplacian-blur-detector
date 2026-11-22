# Browser acceptance — Maintainer Manual Browser QA Passed

On **2026-11-23 (Asia/Taipei)**, the maintainer directly reported completing
browser tests of EXIF rotation, heatmap, Laplacian/Tenengrad switching, opacity,
hover, quality diagnostics, the 390px mobile layout, error handling and batch
workflow, with no abnormalities found. **Maintainer Manual Browser QA Passed**
applies to that reported scope.

This is **maintainer-reported manual acceptance**, separate from automated numeric,
API and controller tests. Codex did not operate the browser for this acceptance.
The earlier automation inventory attempt on 2026-11-22 timed out; it is historical
tooling evidence, not the source of this pass. No browser binding was retried.

| Provenance | Supplied evidence |
| --- | --- |
| Reporter/date | Maintainer's direct report, recorded 2026-11-23 |
| Result | No abnormalities found in the reported feature categories |
| Mobile width | 390px mobile layout reported |
| Exact session date/time | Not supplied; the date above records the maintainer's report |
| Browser/version, OS, device pixel ratio | Not supplied |
| Exact tested commit/build | Not supplied; the reviewed runtime baseline is `df1e564`, but this is not claimed to be the exact tested SHA |
| Exact desktop width / 1280px | Not supplied |
| Physical touch device vs emulation | Not supplied; 390px layout alone does not prove real touch testing |
| Keyboard-only checks | Not separately reported |
| Screenshots / recording | Not supplied; no screenshot or synthetic illustration is substituted |

| Maintainer-reported category | Result |
| --- | --- |
| EXIF rotation | Passed, reported |
| Heatmap | Passed, reported |
| Laplacian/Tenengrad switching | Passed, reported |
| Opacity | Passed, reported |
| Hover | Passed, reported |
| Quality Diagnostics | Passed, reported |
| 390px mobile layout | Passed, reported |
| Error handling | Passed, reported |
| Batch workflow | Passed, reported |

The maintainer can decide whether browser/build provenance, real touch, keyboard,
all EXIF mirror variants, low-texture hatching, throttled stale responses and
individual policy/busy-error cases need additional acceptance before the intended
experimental release. They were not individually documented in the report and
must not be silently marked as independently executed or failed.

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

## Detailed repeatable protocol (not a record that every substep was reported)

The following detailed protocol remains available for supplemental acceptance.
Unreported details below are not independently documented; they do not revoke
the maintainer's category-level pass above.

| Check | Required observation | Report mapping / supplemental evidence |
| --- | --- | --- |
| Layout | Controls, diagnostics text/policy editor and image fit without horizontal page overflow; mobile controls remain usable | 390px category passed; exact desktop width not supplied |
| Original/Heatmap | Demo shows original and aligned SVG overlay; first/middle/last cells cover the image with no shift or stretched margins | Heatmap passed; exact cell sampling not documented |
| Relative mapping | Both metrics update the legend/raw scores; label says Relative Sharpness, never blur localization or cross-image normalization | Metric switching passed; individual legend semantics not separately reported |
| Opacity | Set 0/55/100 using pointer and keyboard; original remains visible at 0, regions align at each setting | Passed; exact values/keyboard method not supplied |
| Hover | Pointer over corners/center gives matching x/y/width/height, metric score and texture information | Passed; exact positions/values not supplied |
| Keyboard | Tab to the overlay/controls, use documented arrow navigation; focus and cell information are visible without a mouse | Not separately reported |
| Touch | Tap cells on phone; details persist/readable without hover; scrolling still works | Physical touch/device not supplied |
| Low texture | `flat.png` has separate hatching/insufficient evidence, no Blurry rejection; demo flat regions also distinct | Not separately reported |
| Dimensions | Portrait and 1027×773 images retain aspect ratio, complete grid remainder coverage, correct displayed coordinates | Odd-size substeps not separately reported |
| EXIF | Each `exif-2.jpg`…`exif-8.jpg` preview matches its `reference-exif-N.png`; heatmap coordinates and quality dimensions follow displayed orientation | Rotation passed; each mirror variant not individually documented |
| Diagnostics | `{}` gives measurements without enabled warning rules; loading example hints gives the demo resolution warning, limitations and suggestion | Diagnostics passed; each policy scenario not separately documented |
| Policy errors | Invalid/duplicate JSON or wrong intensity scale gives readable errors; correcting it and retrying succeeds without old hints | Error handling passed; exact policy subcases not supplied |
| API errors/retry | Stop the local server or use DevTools Offline, request analysis, observe error and cleared stale output; restore service/network and retry | Error handling passed; offline/busy subcases not individually documented |
| Stale responses | With DevTools throttling, rapidly select different images and metrics, edit policy and clear selection; old maps/hints must never repaint the latest selection | Throttled race substeps not separately reported |
| Batch compatibility | Start/cancel/resume a batch and retry failed files; counters, threshold decisions and CSV remain independent of heatmap/diagnostic settings | Batch flow passed; each cancellation/export substep not individually documented |

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
Supplement this report only with actual observations, recording who performed
them. The maintainer's scoped acceptance is recorded in [release gates](RELEASE_READINESS.md);
remaining evidence/coverage choices are explicit maintainer decisions.
