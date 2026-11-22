// Relative values are for this image/metric/grid only, never a calibrated score.
export function relativeScale(cells) {
  let minimum = Infinity, maximum = -Infinity;
  for (const cell of cells) {
    if (!Number.isFinite(cell.sharpness_score) || cell.sharpness_score < 0) throw new Error("Invalid sharpness score.");
    if (!cell.is_low_texture) {
      minimum = Math.min(minimum, cell.sharpness_score);
      maximum = Math.max(maximum, cell.sharpness_score);
    }
  }
  const available = minimum !== Infinity;
  return {
    minimum: available ? minimum : null, maximum: available ? maximum : null,
    values: cells.map((cell) => cell.is_low_texture ? null : maximum === minimum ? 0.5
      : Math.max(0, Math.min(1, (cell.sharpness_score - minimum) / (maximum - minimum)))),
  };
}

export function relativeColor(value) {
  // Blue -> teal -> yellow: no red/green pass/fail semantics.
  const stops = [[49, 54, 149], [32, 178, 170], [253, 231, 37]];
  const t = Math.max(0, Math.min(1, value));
  const index = t < 0.5 ? 0 : 1;
  const fraction = (t - index * 0.5) * 2;
  return `rgb(${stops[index].map((channel, i) => Math.round(channel + (stops[index + 1][i] - channel) * fraction)).join(", ")})`;
}

export function validLocalResult(payload) {
  if (payload?.success !== true || !["laplacian", "tenengrad"].includes(payload.metric)) return false;
  if (![payload.width, payload.height, payload.grid_rows, payload.grid_columns].every((v) => Number.isSafeInteger(v) && v > 0)) return false;
  if (payload.grid_rows > 32 || payload.grid_columns > 32 || !Array.isArray(payload.cells)
    || payload.cells.length !== payload.grid_rows * payload.grid_columns) return false;
  return payload.cells.every((cell, index) => {
    const row = Math.floor(index / payload.grid_columns), column = index % payload.grid_columns;
    const x = Math.floor(column * payload.width / payload.grid_columns), y = Math.floor(row * payload.height / payload.grid_rows);
    return cell.row === row && cell.column === column && cell.x === x && cell.y === y
      && cell.width === Math.floor((column + 1) * payload.width / payload.grid_columns) - x
      && cell.height === Math.floor((row + 1) * payload.height / payload.grid_rows) - y
      && cell.width > 0 && cell.height > 0 && cell.metric === payload.metric
      && [cell.sharpness_score, cell.texture_std].every((v) => Number.isFinite(v) && v >= 0)
      && typeof cell.is_low_texture === "boolean";
  });
}

const format = (value) => value >= 1e6 || (value > 0 && value < 0.01) ? value.toExponential(3) : value.toFixed(2);
export function cellDescription(cell) {
  return `Region (${cell.column}, ${cell.row}) · x ${cell.x}, y ${cell.y} · ${cell.width} × ${cell.height} px\n`
    + `${cell.metric === "tenengrad" ? "Tenengrad" : "Laplacian"} score ${format(cell.sharpness_score)} · Texture std ${format(cell.texture_std)}\n`
    + (cell.is_low_texture ? "Low texture — insufficient evidence to assess blur." : "Texture above cutoff — not a sharpness guarantee.");
}

export function mountHeatmap(doc = document, request = fetch) {
  const ids = ["heatmap-overlay", "view-original", "view-heatmap", "local-metric", "grid-rows", "grid-columns",
    "texture-cutoff", "heatmap-opacity", "opacity-value", "heatmap-status", "heatmap-legend", "heatmap-range", "cell-information"];
  const [overlay, original, heatmap, metric, rows, columns, cutoff, opacity, opacityValue, status, legend, range, info] = ids.map((id) => doc.getElementById(id));
  let file = null, result = null, loading = false, busy = false, generation = 0, controller = null, mode = "original", activeCell = -1;
  let rectangles = [];
  const svgElement = (name, attributes = {}) => {
    const element = doc.createElementNS("http://www.w3.org/2000/svg", name);
    for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, String(value));
    return element;
  };
  function controls() {
    original.disabled = !file;
    heatmap.disabled = !file || busy || loading;
    heatmap.textContent = loading ? "Loading…" : "Heatmap";
    for (const input of [metric, rows, columns, cutoff]) input.disabled = !file || busy;
    original.setAttribute("aria-pressed", String(mode === "original"));
    heatmap.setAttribute("aria-pressed", String(mode === "heatmap"));
    overlay.toggleAttribute("hidden", mode !== "heatmap" || !result);
    legend.hidden = !result || mode !== "heatmap";
    opacity.disabled = mode !== "heatmap" || !result;
  }
  function cancelRequest() { generation++; controller?.abort(); controller = null; loading = false; }
  function inspect(index) {
    if (activeCell >= 0) rectangles[activeCell]?.classList.remove("active-cell");
    activeCell = index;
    if (index >= 0 && result) {
      rectangles[index]?.classList.add("active-cell");
      info.textContent = cellDescription(result.cells[index]);
    } else info.textContent = "Hover or tap a cell. Focus the heatmap and use arrow keys to inspect regions.";
  }
  function showOriginal() {
    cancelRequest(); mode = "original"; inspect(-1); controls();
    status.textContent = file ? "Original view. Select Heatmap to inspect local measurements." : "Select an image to explore relative sharpness.";
  }
  function draw() {
    overlay.replaceChildren(); rectangles = [];
    overlay.setAttribute("viewBox", `0 0 ${result.width} ${result.height}`);
    const defs = svgElement("defs");
    const pattern = svgElement("pattern", { id: "low-texture-hatch", width: 12, height: 12, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" });
    pattern.append(svgElement("rect", { width: 12, height: 12, fill: "#334155" }),
      svgElement("line", { x1: 0, y1: 0, x2: 0, y2: 12, stroke: "#f8fafc", "stroke-width": 4 }));
    defs.append(pattern); overlay.append(defs);
    const scale = relativeScale(result.cells);
    result.cells.forEach((cell, index) => {
      const rect = svgElement("rect", { x: cell.x, y: cell.y, width: cell.width, height: cell.height,
        fill: scale.values[index] === null ? "url(#low-texture-hatch)" : relativeColor(scale.values[index]),
        "data-cell-index": index, "vector-effect": "non-scaling-stroke" });
      rectangles.push(rect); overlay.append(rect);
    });
    range.textContent = scale.minimum === null ? "No cells above texture cutoff; color scale unavailable."
      : scale.minimum === scale.maximum ? `All textured cells equal: ${format(scale.minimum)} (midpoint color).`
      : `Raw score range: ${format(scale.minimum)} – ${format(scale.maximum)} · ${result.metric}`;
    inspect(-1);
    status.textContent = `${result.grid_rows} × ${result.grid_columns} regions · ${result.width} × ${result.height} px · ${result.cells.filter((cell) => cell.is_low_texture).length} low-texture cells.`;
    controls();
  }
  function validSettings() {
    return [rows, columns].every((input) => input.value.trim() && Number.isInteger(Number(input.value)) && Number(input.value) >= 1 && Number(input.value) <= 32)
      && cutoff.value.trim() && Number.isFinite(Number(cutoff.value)) && Number(cutoff.value) >= 0;
  }
  async function showHeatmap() {
    if (!file || busy || loading) return;
    if (result) { mode = "heatmap"; draw(); return; }
    if (!validSettings()) { status.textContent = "Use 1–32 rows/columns and a finite, non-negative texture cutoff."; return; }
    cancelRequest(); const current = generation;
    controller = new AbortController(); const requestController = controller; const signal = controller.signal;
    let timedOut = false;
    const timer = setTimeout(() => { timedOut = true; requestController.abort(); }, 30000);
    loading = true; status.textContent = "Calculating full-image responses and local statistics…"; controls();
    try {
      const data = new FormData(); data.append("image", file);
      data.append("metric", metric.value); data.append("grid_rows", rows.value); data.append("grid_columns", columns.value);
      data.append("min_texture_std", cutoff.value);
      const response = await request("/api/sharpness/local", { method: "POST", body: data, signal });
      const payload = await response.json();
      if (current !== generation) return;
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : `Local analysis failed (HTTP ${response.status}).`);
      if (!validLocalResult(payload)) throw new Error("Incomplete local analysis response. Please retry.");
      result = payload; mode = "heatmap"; draw();
    } catch (error) {
      if (current !== generation) return;
      mode = "original"; result = null; overlay.replaceChildren();
      status.textContent = timedOut ? "Local analysis timed out after 30 seconds. Select Heatmap to retry."
        : `${error.message || "Could not reach the service."} Select Heatmap to retry.`;
    } finally {
      clearTimeout(timer);
      if (current === generation) { loading = false; controller = null; controls(); }
    }
  }
  original.addEventListener("click", showOriginal);
  heatmap.addEventListener("click", showHeatmap);
  for (const input of [metric, rows, columns, cutoff]) input.addEventListener("change", () => {
    const refresh = mode === "heatmap" || loading;
    cancelRequest(); result = null; mode = "original"; overlay.replaceChildren(); inspect(-1); controls();
    if (refresh) void showHeatmap();
  });
  opacity.addEventListener("input", () => {
    overlay.style.opacity = String(Number(opacity.value) / 100);
    opacityValue.textContent = `${opacity.value}%`;
  });
  overlay.style.opacity = String(Number(opacity.value) / 100);
  overlay.addEventListener("pointermove", (event) => {
    const index = event.target.getAttribute("data-cell-index");
    inspect(index === null ? -1 : Number(index));
  });
  overlay.addEventListener("click", (event) => {
    const index = event.target.getAttribute("data-cell-index");
    if (index !== null) inspect(Number(index));
  });
  overlay.addEventListener("pointerleave", () => inspect(-1));
  overlay.addEventListener("focus", () => { if (result) inspect(0); });
  overlay.addEventListener("keydown", (event) => {
    if (!result) return;
    const offsets = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -result.grid_columns, ArrowDown: result.grid_columns };
    if (!(event.key in offsets)) return;
    event.preventDefault();
    inspect(Math.max(0, Math.min(result.cells.length - 1, Math.max(0, activeCell) + offsets[event.key])));
  });
  showOriginal();
  return {
    setFile(nextFile) {
      cancelRequest(); file = nextFile; result = null; mode = "original"; rectangles = [];
      overlay.replaceChildren(); showOriginal();
    },
    setBatchBusy(value) { if (busy === value) return; busy = value; if (busy && loading) showOriginal(); controls(); },
    destroy() { cancelRequest(); },
  };
}
