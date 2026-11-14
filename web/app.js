"use strict";

/** Return a required page element or fail immediately with its missing ID. */
function requireElement(id) {
  const element = document.getElementById(id);
  if (!element) throw new Error(`Missing required DOM element: #${id}`);
  return element;
}

const input = requireElement("image-input");
const dropZone = requireElement("drop-zone");
const preview = requireElement("image-preview");
const previewWrap = requireElement("preview-wrap");
const selectedFilename = requireElement("selected-filename");
const changeImageButton = requireElement("change-image-button");
const thresholdInput = requireElement("threshold-input");
const thresholdValue = requireElement("threshold-value");
const analyzeButton = requireElement("analyze-button");
const resultLabel = requireElement("result-label");
const resultBadge = requireElement("result-badge");
const resultMessage = requireElement("result-message");
const resultDetails = requireElement("result-details");
const apiResponse = requireElement("api-response");
const rawResponse = requireElement("raw-response");
const metricScore = requireElement("metric-score");
const metricThreshold = requireElement("metric-threshold");
const metricResolution = requireElement("metric-resolution");
const metricSize = requireElement("metric-size");
const barScore = requireElement("bar-score");
const scoreTrack = requireElement("score-track");
const thresholdMarker = requireElement("threshold-marker");
const scoreMarker = requireElement("score-marker");
const scaleThreshold = requireElement("scale-threshold");
const scaleMaximum = requireElement("scale-maximum");

let selectedFile = null;
let previewUrl = null;

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function resetResult() {
  resultLabel.textContent = "No analysis yet";
  resultMessage.textContent = "Upload an image and run analysis.";
  resultBadge.textContent = "PENDING";
  resultBadge.className = "result-badge neutral";
  resultDetails.hidden = true;
  apiResponse.hidden = true;
  rawResponse.textContent = "";
}

function selectFile(file) {
  if (!file || !["image/jpeg", "image/png"].includes(file.type)) return;

  selectedFile = file;
  analyzeButton.disabled = false;
  selectedFilename.textContent = file.name;
  changeImageButton.hidden = false;
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = URL.createObjectURL(file);
  preview.src = previewUrl;
  previewWrap.hidden = false;
  dropZone.hidden = true;
  resetResult();
}

function renderResult(payload) {
  const isBlurry = payload.is_blurry;
  const resultWord = isBlurry ? "BLURRY" : "CLEAR";
  resultLabel.textContent = resultWord;
  resultMessage.textContent = payload.message;
  resultBadge.textContent = resultWord;
  resultBadge.className = `result-badge ${isBlurry ? "blurry" : "clear"}`;

  metricScore.textContent = payload.blur_score.toFixed(2);
  metricThreshold.textContent = payload.threshold.toFixed(2);
  metricResolution.textContent = `${payload.width} × ${payload.height}`;
  metricSize.textContent = formatBytes(payload.file_size);
  barScore.textContent = payload.blur_score.toFixed(2);

  const displayMaximum = Math.max(200, payload.threshold * 2, payload.blur_score * 1.15);
  const thresholdPosition = Math.min(100, (payload.threshold / displayMaximum) * 100);
  const scorePosition = Math.min(100, (payload.blur_score / displayMaximum) * 100);
  scoreTrack.style.setProperty("--threshold-position", `${thresholdPosition}%`);
  thresholdMarker.style.left = `${thresholdPosition}%`;
  scoreMarker.style.left = `${scorePosition}%`;
  scaleThreshold.textContent = payload.threshold.toFixed(0);
  scaleMaximum.textContent = `${Math.ceil(displayMaximum)}+`;

  resultDetails.hidden = false;
  apiResponse.hidden = false;
  rawResponse.textContent = JSON.stringify(payload, null, 2);
}

async function analyze() {
  if (!selectedFile) return;

  const data = new FormData();
  data.append("image", selectedFile);
  data.append("threshold", thresholdInput.value);
  analyzeButton.disabled = true;
  analyzeButton.textContent = "Analyzing...";

  try {
    const response = await fetch("/api/blur/check", { method: "POST", body: data });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Image analysis failed.");
    renderResult(payload);
  } catch (error) {
    alert(error.message || "Image analysis failed.");
  } finally {
    analyzeButton.disabled = false;
    analyzeButton.textContent = "Analyze image";
  }
}

input.addEventListener("change", () => selectFile(input.files[0]));
changeImageButton.addEventListener("click", () => input.click());
thresholdInput.addEventListener("input", () => {
  thresholdValue.textContent = Number(thresholdInput.value).toFixed(2);
});
analyzeButton.addEventListener("click", analyze);

["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("dragging");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("dragging");
  });
});

dropZone.addEventListener("drop", (event) => selectFile(event.dataTransfer.files[0]));
