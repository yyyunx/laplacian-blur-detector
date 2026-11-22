import { resultStatus, resultsCsv, sortResults } from "./batch-utils.js";
import { mountHeatmap } from "./heatmap.js";
import { mountQualityDiagnostics } from "./quality-diagnostics.js";

const localHeatmap = mountHeatmap();
const qualityDiagnostics = mountQualityDiagnostics();

const get = (id) => {
  const element = document.getElementById(id);
  if (!element) throw new Error(`Missing required element: ${id}`);
  return element;
};
const ui = {
  input: get("image-input"), surface: get("upload-surface"), drop: get("drop-zone"),
  preview: get("image-preview"), previewWrap: get("preview-wrap"), filename: get("selected-filename"),
  add: get("change-image-button"), threshold: get("threshold-input"), analyze: get("analyze-button"),
  retry: get("retry-button"), cancel: get("cancel-button"), clear: get("clear-button"),
  export: get("export-button"), message: get("upload-message"), limits: get("upload-limits"),
  label: get("result-label"), badge: get("result-badge"), detailMessage: get("result-message"),
  details: get("result-details"), rawPanel: get("api-response"), raw: get("raw-response"),
  score: get("metric-score"), resultThreshold: get("metric-threshold"), resolution: get("metric-resolution"),
  size: get("metric-size"), barScore: get("bar-score"), track: get("score-track"),
  thresholdMarker: get("threshold-marker"), scoreMarker: get("score-marker"),
  scaleThreshold: get("scale-threshold"), scaleMaximum: get("scale-maximum"),
  total: get("count-total"), clearCount: get("count-clear"), blurryCount: get("count-blurry"),
  errorCount: get("count-error"), progress: get("analysis-progress"), progressLabel: get("progress-label"),
  filter: get("status-filter"), sort: get("sort-order"), rows: get("batch-results"),
  demo: get("demo-button"),
};
let items = [];
let selectedId = null;
let nextId = 0;
let previewUrl = null;
let running = false;
let demoLoading = false;
let cancelRequested = false;
let activeController = null;
let runMessage = "";
let limits = { max_upload_bytes: 10 * 1024 * 1024, max_batch_files: 20, max_image_pixels: 20_000_000 };

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KiB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MiB`;
}
function formatScore(value) {
  return value >= 1e6 || (value > 0 && value < 0.01) ? value.toExponential(2) : value.toFixed(2);
}
function showMessage(message = "") {
  ui.message.textContent = message;
  ui.message.hidden = !message;
}
function fileProblem(file) {
  if (!/\.(jpe?g|png)$/iu.test(file.name)) return "Unsupported format. Choose a JPG, JPEG, or PNG.";
  if (!file.size) return "This file is empty.";
  if (file.size > limits.max_upload_bytes) return `File exceeds the ${formatBytes(limits.max_upload_bytes)} limit.`;
  return "";
}
function validThreshold() {
  return ui.threshold.value.trim() !== "" && Number.isFinite(Number(ui.threshold.value)) && Number(ui.threshold.value) >= 0;
}
function releasePreview() {
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = null;
  ui.preview.removeAttribute("src");
}
function selectItem(id) {
  selectedId = id;
  releasePreview();
  const item = items.find((entry) => entry.id === id);
  const canPreview = item?.valid && item.errorCode !== "IMAGE_TOO_LARGE";
  localHeatmap.setFile(canPreview ? item.file : null);
  qualityDiagnostics.setFile(canPreview ? item.file : null);
  ui.previewWrap.hidden = !canPreview;
  ui.drop.hidden = !!canPreview;
  if (canPreview) {
    previewUrl = URL.createObjectURL(item.file);
    ui.preview.src = previewUrl;
  }
  renderQueue();
}
function resetItem(item) {
  item.status = item.valid ? "pending" : "error";
  item.result = null;
  item.response = null;
  item.error = item.valid ? "" : fileProblem(item.file);
  item.errorCode = "";
}
function addFiles(files) {
  if (running) { showMessage("Finish or cancel the current analysis before adding images."); return; }
  const messages = [];
  for (const file of files) {
    if (items.length >= limits.max_batch_files) {
      messages.push(`The queue holds up to ${limits.max_batch_files} files. Extra files were not added.`);
      break;
    }
    const error = fileProblem(file);
    items.push({ id: nextId++, file, valid: !error, status: error ? "error" : "pending", error, errorCode: "", result: null, response: null });
  }
  runMessage = "";
  ui.input.value = "";
  showMessage(messages.join(" "));
  if (selectedId === null && items.length) selectItem(items[0].id);
  else renderQueue();
}
function renderDetail() {
  const item = items.find((entry) => entry.id === selectedId);
  ui.filename.textContent = item ? item.file.name : "No image selected";
  ui.details.hidden = true;
  ui.rawPanel.hidden = !item?.response;
  ui.raw.textContent = item?.response ? JSON.stringify(item.response, null, 2) : "";
  if (!item || item.status !== "done") {
    ui.label.textContent = item?.status === "error" ? "Could not analyze" : item?.status === "analyzing" ? "Analyzing image..." : "No analysis yet";
    ui.badge.textContent = item?.status === "error" ? "FAILED" : item?.status === "analyzing" ? "RUNNING" : "PENDING";
    ui.badge.className = `result-badge ${item?.status === "error" ? "error" : "neutral"}`;
    ui.detailMessage.textContent = item?.error || "Choose images, then run analysis.";
    return;
  }
  const result = item.result;
  const word = result.is_blurry ? "BLURRY" : "CLEAR";
  ui.label.textContent = word;
  ui.badge.textContent = word;
  ui.badge.className = `result-badge ${result.is_blurry ? "blurry" : "clear"}`;
  ui.detailMessage.textContent = result.message;
  ui.score.textContent = formatScore(result.blur_score);
  ui.resultThreshold.textContent = formatScore(result.threshold);
  ui.resolution.textContent = `${result.width} \u00d7 ${result.height}`;
  ui.size.textContent = formatBytes(result.file_size);
  ui.barScore.textContent = formatScore(result.blur_score);
  const largest = Math.max(200, result.threshold, result.blur_score);
  const maximum = largest <= Number.MAX_VALUE / 1.15 ? largest * 1.15 : largest;
  const thresholdPosition = (result.threshold / maximum) * 100;
  ui.track.style.setProperty("--threshold-position", `${thresholdPosition}%`);
  ui.thresholdMarker.style.left = `${thresholdPosition}%`;
  ui.scoreMarker.style.left = `${(result.blur_score / maximum) * 100}%`;
  ui.scaleThreshold.textContent = formatScore(result.threshold);
  ui.scaleMaximum.textContent = maximum >= 1e6 ? maximum.toExponential(2) : String(Math.ceil(maximum));
  ui.details.hidden = false;
}
function renderQueue() {
  localHeatmap.setBatchBusy(running);
  qualityDiagnostics.setBatchBusy(running);
  ui.demo.disabled = running || demoLoading || items.length >= limits.max_batch_files;
  const counts = { clear: 0, blurry: 0, error: 0, pending: 0, analyzing: 0 };
  for (const item of items) counts[resultStatus(item)]++;
  ui.total.textContent = String(items.length);
  ui.clearCount.textContent = String(counts.clear);
  ui.blurryCount.textContent = String(counts.blurry);
  ui.errorCount.textContent = String(counts.error);
  const completed = counts.clear + counts.blurry + counts.error;
  ui.progress.max = items.length || 1;
  ui.progress.value = completed;
  ui.progressLabel.textContent = running ? `${completed} of ${items.length} finished - analyzing...` : runMessage || (items.length ? `${completed} of ${items.length} finished` : "Add images to get started.");
  ui.input.disabled = ui.add.disabled = ui.threshold.disabled = running;
  ui.clear.disabled = running || !items.length;
  ui.export.disabled = !items.length;
  ui.cancel.hidden = !running;
  ui.cancel.disabled = cancelRequested;
  ui.analyze.disabled = running || !validThreshold() || !items.some((item) => item.valid);
  ui.analyze.textContent = running ? "Analyzing..." : !items.length ? "Analyze images" : counts.pending ? "Analyze pending" : "Reanalyze all";
  ui.retry.hidden = !items.some((item) => item.status === "error" && item.valid);
  ui.retry.disabled = running || !validThreshold();
  const visible = sortResults(items, ui.sort.value).filter((item) => {
    if (ui.filter.value === "all") return true;
    if (ui.filter.value === "pending") return ["pending", "analyzing"].includes(item.status);
    return resultStatus(item) === ui.filter.value;
  });
  ui.rows.replaceChildren();
  if (!visible.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 6; cell.className = "empty-row";
    cell.textContent = items.length ? "No images match this filter." : "Your results will appear here.";
    row.append(cell); ui.rows.append(row);
  }
  for (const item of visible) {
    const row = document.createElement("tr");
    row.className = item.id === selectedId ? "is-selected" : "";
    const nameCell = document.createElement("td");
    const name = document.createElement("button");
    name.type = "button"; name.className = "filename-button"; name.textContent = item.file.name;
    name.title = item.error || item.file.name;
    name.setAttribute("aria-pressed", String(item.id === selectedId));
    name.addEventListener("click", () => selectItem(item.id)); nameCell.append(name);
    if (item.error) { const note = document.createElement("small"); note.textContent = item.error; nameCell.append(note); }
    const statusCell = document.createElement("td");
    const badge = document.createElement("span");
    const status = resultStatus(item);
    badge.className = `result-badge ${["clear", "blurry", "error"].includes(status) ? status : "neutral"}`;
    badge.textContent = status === "error" ? "FAILED" : status.toUpperCase(); statusCell.append(badge);
    row.append(nameCell, statusCell);
    for (const text of [item.result ? formatScore(item.result.blur_score) : "--", item.result ? `${item.result.width} \u00d7 ${item.result.height}` : "--", formatBytes(item.file.size)]) {
      const cell = document.createElement("td"); cell.textContent = text; row.append(cell);
    }
    const action = document.createElement("td");
    const remove = document.createElement("button");
    remove.type = "button"; remove.className = "text-button"; remove.textContent = "Remove";
    remove.disabled = running; remove.setAttribute("aria-label", `Remove ${item.file.name}`);
    remove.addEventListener("click", () => {
      items = items.filter((entry) => entry.id !== item.id); runMessage = "";
      if (selectedId === item.id) selectItem(items[0]?.id ?? null); else renderQueue();
    });
    action.append(remove); row.append(action); ui.rows.append(row);
  }
  renderDetail();
}
function validResult(payload) {
  return payload?.success === true && typeof payload.is_blurry === "boolean"
    && [payload.blur_score, payload.threshold].every((value) => Number.isFinite(value) && value >= 0)
    && [payload.width, payload.height, payload.file_size].every((value) => Number.isFinite(value) && value > 0)
    && typeof payload.message === "string";
}
async function analyze(retryOnly = false) {
  if (running || !validThreshold()) return;
  let targets;
  if (retryOnly) {
    targets = items.filter((item) => item.status === "error" && item.valid);
    for (const item of targets) resetItem(item);
  } else {
    if (!items.some((item) => item.status === "pending")) {
      for (const item of items) if (item.valid) resetItem(item);
    }
    targets = items.filter((item) => item.status === "pending");
  }
  if (!targets.length) return;
  const threshold = Number(ui.threshold.value);
  running = true; cancelRequested = false; runMessage = ""; showMessage();
  renderQueue();
  try {
    for (const item of targets) {
      if (cancelRequested) break;
      item.status = "analyzing"; renderQueue();
      const controller = new AbortController(); activeController = controller;
      let timedOut = false;
      const timeout = setTimeout(() => { timedOut = true; controller.abort(); }, 30000);
      try {
        const data = new FormData(); data.append("image", item.file); data.append("threshold", String(threshold));
        const response = await fetch("/api/blur/check", { method: "POST", body: data, signal: controller.signal });
        const text = await response.text();
        let payload;
        try { payload = JSON.parse(text); } catch { throw new Error(`The service returned an unreadable response (HTTP ${response.status}). Please retry.`); }
        if (cancelRequested) { resetItem(item); break; }
        item.response = payload;
        if (!response.ok) {
          const detail = typeof payload.detail === "string" ? payload.detail : `Image analysis failed (HTTP ${response.status}).`;
          throw Object.assign(new Error(detail), { code: payload.error_code });
        }
        if (!validResult(payload)) throw new Error("The service returned an incomplete result. Please retry.");
        item.result = payload; item.status = "done"; item.error = "";
      } catch (error) {
        if (cancelRequested) { resetItem(item); break; }
        item.status = "error";
        item.error = timedOut ? "Analysis timed out after 30 seconds. Please retry." : error.message || "Could not reach the service. Please retry.";
        item.errorCode = timedOut ? "TIMEOUT" : error.code || "ANALYSIS_FAILED";
        if (item.errorCode === "IMAGE_TOO_LARGE" && item.id === selectedId) {
          localHeatmap.setFile(null);
          qualityDiagnostics.setFile(null);
          releasePreview(); ui.previewWrap.hidden = true; ui.drop.hidden = false;
        }
      } finally {
        clearTimeout(timeout); activeController = null; renderQueue();
      }
    }
  } finally {
    running = false;
    runMessage = cancelRequested ? "Cancelled. Finished results are kept; remaining images can be resumed." : "Analysis finished. Select an image to inspect its result.";
    renderQueue();
  }
}

ui.input.addEventListener("change", () => addFiles(ui.input.files));
ui.demo.addEventListener("click", async () => {
  if (running || demoLoading) return;
  demoLoading = true; renderQueue();
  try {
    const response = await fetch("/static/demo.png");
    if (!response.ok) throw new Error("Could not load the generated demo image.");
    const file = new File([await response.blob()], "sharpness-demo.png", { type: "image/png" });
    if (running) return;
    addFiles([file]); selectItem(items[items.length - 1].id);
  } catch (error) { showMessage(error.message); }
  finally { demoLoading = false; renderQueue(); }
});
ui.add.addEventListener("click", () => ui.input.click());
ui.drop.addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") { event.preventDefault(); if (!running) ui.input.click(); }
});
ui.analyze.addEventListener("click", () => analyze());
ui.retry.addEventListener("click", () => analyze(true));
ui.cancel.addEventListener("click", () => { cancelRequested = true; activeController?.abort(); renderQueue(); });
ui.threshold.addEventListener("input", () => {
  if (running) return;
  for (const item of items) resetItem(item);
  runMessage = items.length ? "Threshold changed. Run analysis again to refresh the results." : "";
  renderQueue();
});
ui.filter.addEventListener("change", renderQueue);
ui.sort.addEventListener("change", renderQueue);
ui.clear.addEventListener("click", () => {
  if (running) return;
  items = []; selectedId = null; runMessage = ""; ui.input.value = "";
  ui.filter.value = "all"; ui.sort.value = "added"; showMessage(); selectItem(null);
});
ui.export.addEventListener("click", () => {
  const url = URL.createObjectURL(new Blob(["\ufeff", resultsCsv(sortResults(items, ui.sort.value))], { type: "text/csv;charset=utf-8;" }));
  const link = document.createElement("a"); link.href = url; link.download = "blur-results.csv";
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
for (const eventName of ["dragenter", "dragover"]) {
  ui.surface.addEventListener(eventName, (event) => { event.preventDefault(); ui.surface.classList.add("dragging"); });
}
for (const eventName of ["dragleave", "drop"]) {
  ui.surface.addEventListener(eventName, (event) => { event.preventDefault(); ui.surface.classList.remove("dragging"); });
}
ui.surface.addEventListener("drop", (event) => { event.stopPropagation(); addFiles(event.dataTransfer.files); });
window.addEventListener("dragover", (event) => event.preventDefault());
window.addEventListener("drop", (event) => event.preventDefault());
window.addEventListener("beforeunload", () => { releasePreview(); activeController?.abort(); localHeatmap.destroy(); qualityDiagnostics.destroy(); });
ui.preview.addEventListener("error", () => { ui.previewWrap.hidden = true; ui.drop.hidden = false; localHeatmap.setFile(null); qualityDiagnostics.setFile(null); });
renderQueue();
fetch("/api/config").then((response) => {
  if (!response.ok) throw new Error("Unavailable");
  return response.json();
}).then((config) => {
  for (const key of ["max_upload_bytes", "max_batch_files", "max_image_pixels"]) {
    if (!Number.isSafeInteger(config[key]) || config[key] <= 0) throw new Error("Invalid limits");
  }
  limits = config;
  ui.limits.textContent = `Up to ${limits.max_batch_files} files - ${formatBytes(limits.max_upload_bytes)} each - ${limits.max_image_pixels / 1_000_000} megapixels per image`;
}).catch(() => { if (!items.length) showMessage("Could not reach the service. You can select images and retry analysis."); });
