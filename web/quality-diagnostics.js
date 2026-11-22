const CHECK_NAMES = {
  brightness: "Brightness", underexposure: "Dark pixels", overexposure: "Bright channels",
  resolution: "Resolution", sharpness: "Sharpness", texture: "Texture",
};
const STATUSES = ["not_evaluated", "within_policy", "warning", "informational", "insufficient_evidence"];
const normalized = (v) => Number.isFinite(v) && v >= 0 && v <= 1;
const positiveInteger = (v) => Number.isSafeInteger(v) && v > 0;
const score = (v) => v >= 1e6 || (v > 0 && v < 0.01) ? v.toExponential(2) : v.toFixed(2);
const intensity = (v) => v > 0 && v < 0.001 ? v.toExponential(2) : v.toFixed(3);
const ratio = (v) => `${v > 0 && v < 0.001 ? (v * 100).toExponential(2) : (v * 100).toFixed(1)}%`;

export function exampleDiagnosticPolicy() {
  // Explicit opt-in illustration. These are not universal acceptance thresholds.
  return { min_mean_brightness: 0.2, max_dark_ratio: 0.5, max_bright_ratio: 0.2, min_width: 1024, min_height: 768 };
}

export function validQualityResult(payload) {
  if (payload?.success !== true || payload.schema_version !== 1) return false;
  const { brightness: b, exposure: e, resolution: r, sharpness: s } = payload.measurements || {};
  if (!b || !e || !r || !s) return false;
  if (![b.mean, b.median, e.dark_pixel_ratio, e.bright_pixel_ratio, e.dark_pixel_cutoff, e.bright_pixel_cutoff, s.texture_std_normalized].every(normalized)) return false;
  if (![r.width, r.height, r.pixels].every(positiveInteger) || r.pixels !== r.width * r.height
    || payload.width !== r.width || payload.height !== r.height) return false;
  if (![s.laplacian_score, s.tenengrad_score, s.texture_std].every((v) => Number.isFinite(v) && v >= 0)
    || ![1, 255, 65535].includes(s.input_intensity_max) || typeof s.is_low_texture !== "boolean") return false;
  if (!payload.policy || typeof payload.policy !== "object" || Array.isArray(payload.policy)) return false;
  if (!Array.isArray(payload.limitations) || !payload.limitations.every((v) => typeof v === "string")) return false;
  return Object.keys(CHECK_NAMES).every((name) => {
    const check = payload.checks?.[name];
    return check && STATUSES.includes(check.status) && typeof check.message === "string"
      && typeof check.limitation === "string" && (check.suggestion === null || typeof check.suggestion === "string");
  });
}

export function mountQualityDiagnostics(doc = document, request = fetch) {
  const get = (id) => doc.getElementById(id);
  const ui = {
    run: get("quality-run"), policy: get("quality-policy"), example: get("quality-example"), reset: get("quality-reset"),
    status: get("quality-status"), results: get("quality-results"), metrics: get("quality-metrics"),
    summary: get("quality-summary"), warnings: get("quality-warnings"), suggestions: get("quality-suggestions"),
    definitions: get("quality-definitions"),
  };
  let file = null, busy = false, loading = false, generation = 0, controller = null;
  function controls() {
    ui.run.disabled = !file || busy || loading;
    ui.run.textContent = loading ? "Measuring…" : "Measure quality";
    ui.run.setAttribute("aria-busy", String(loading));
    for (const element of [ui.policy, ui.example, ui.reset]) element.disabled = busy;
  }
  function invalidate(message = "Policy changed. Measure quality to apply the displayed settings.") {
    generation++; controller?.abort(); controller = null; loading = false;
    ui.results.hidden = true;
    for (const element of [ui.metrics, ui.warnings, ui.suggestions, ui.definitions]) element.replaceChildren();
    ui.summary.textContent = "";
    ui.status.textContent = file ? message : "Select an image, then measure quality. No image is uploaded until requested.";
    controls();
  }
  function line(parent, text, className = "") {
    const item = doc.createElement("li"); item.textContent = text; item.className = className; parent.append(item);
  }
  function render(payload) {
    const { brightness: b, exposure: e, resolution: r, sharpness: s } = payload.measurements;
    ui.metrics.replaceChildren(); ui.warnings.replaceChildren(); ui.suggestions.replaceChildren(); ui.definitions.replaceChildren();
    for (const [label, value] of [
      ["Mean brightness (0–1)", intensity(b.mean)], ["Median brightness (0–1)", intensity(b.median)],
      [`Dark-pixel ratio (cutoff ${intensity(e.dark_pixel_cutoff)})`, ratio(e.dark_pixel_ratio)],
      [`Bright-channel ratio (cutoff ${intensity(e.bright_pixel_cutoff)})`, ratio(e.bright_pixel_ratio)],
      ["Displayed resolution", `${r.width} × ${r.height}`], ["Texture std (0–1)", intensity(s.texture_std_normalized)],
      ["Laplacian variance (native)", score(s.laplacian_score)], ["Tenengrad energy (native)", score(s.tenengrad_score)],
    ]) {
      const article = doc.createElement("article"), caption = doc.createElement("span"), measurement = doc.createElement("strong");
      caption.textContent = label; measurement.textContent = value; article.append(caption, measurement); ui.metrics.append(article);
    }
    let warnings = 0, suggestions = 0;
    for (const [name, label] of Object.entries(CHECK_NAMES)) {
      const check = payload.checks[name];
      if (check.status === "warning") { warnings++; line(ui.warnings, `${label}: ${check.message}`, "quality-warning"); }
      if (check.status === "insufficient_evidence") line(ui.warnings, `${label}: ${check.message}`, "quality-information");
      if (check.suggestion) { suggestions++; line(ui.suggestions, `${label}: ${check.suggestion}`); }
      line(ui.definitions, `${label} (${check.status.replaceAll("_", " ")}): ${check.message} ${check.limitation}`);
    }
    if (!warnings && !s.is_low_texture) line(ui.warnings, "No warnings from configured rules. Disabled checks are not assessed.");
    if (!suggestions) line(ui.suggestions, "No suggestion from the configured rules. Enable task-specific limits to receive hints.");
    for (const limitation of payload.limitations) line(ui.definitions, limitation);
    line(ui.definitions, `Sharpness uses native input intensity scale 0–${s.input_intensity_max}; do not transfer raw thresholds between metrics or bit depths.`);
    ui.summary.textContent = `${warnings} configured warning(s). Hints do not accept/reject the image or change batch decisions.`;
    ui.results.hidden = false;
    ui.status.textContent = "Measurements ready. Results use the displayed policy; no overall quality pass is implied.";
  }
  async function analyze() {
    if (!file || busy || loading) return;
    let policyText;
    try {
      policyText = ui.policy.value.trim() || "{}";
      if (new TextEncoder().encode(policyText).length > 8192) throw new Error("Policy must be at most 8 KiB UTF-8.");
      const policy = JSON.parse(policyText);
      if (!policy || typeof policy !== "object" || Array.isArray(policy)) throw new Error("Policy must be a JSON object.");
    } catch (error) { invalidate(`Invalid policy: ${error.message}`); return; }
    invalidate("Measuring brightness, exposure, resolution and sharpness…");
    const current = generation, active = new AbortController(); controller = active; loading = true; controls();
    let timedOut = false;
    const timer = setTimeout(() => { timedOut = true; active.abort(); }, 30000);
    try {
      // Preserve duplicate fields and large numeric literals for strict server validation.
      const data = new FormData(); data.append("image", file); data.append("policy", policyText);
      const response = await request("/api/quality/diagnose", { method: "POST", body: data, signal: active.signal });
      const payload = await response.json();
      if (current !== generation) return;
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : `Diagnostics failed (HTTP ${response.status}).`);
      if (!validQualityResult(payload)) throw new Error("Incomplete diagnostic response. Please retry.");
      render(payload);
    } catch (error) {
      if (current !== generation) return;
      ui.results.hidden = true;
      ui.status.textContent = timedOut ? "Diagnostics timed out after 30 seconds. Please retry."
        : `${error.message || "Could not reach the service."} Please retry.`;
    } finally {
      clearTimeout(timer);
      if (current === generation) { loading = false; controller = null; controls(); }
    }
  }
  ui.run.addEventListener("click", analyze);
  ui.policy.addEventListener("input", () => invalidate());
  ui.example.addEventListener("click", () => {
    ui.policy.value = JSON.stringify(exampleDiagnosticPolicy(), null, 2);
    invalidate("Uncalibrated example hints loaded. Customize them for your task, then measure quality.");
  });
  ui.reset.addEventListener("click", () => { ui.policy.value = "{}"; invalidate("Measurements-only policy loaded. Warning limits are disabled."); });
  invalidate();
  return {
    setFile(value) { file = value; invalidate(busy ? "Wait for batch analysis to finish before measuring quality." : "Measure quality to inspect this image. Warning limits are opt-in."); },
    setBatchBusy(value) { if (busy === value) return; busy = value; if (busy && loading) invalidate("Local diagnostics cancelled while batch analysis runs."); controls(); },
    destroy() { generation++; controller?.abort(); },
  };
}
