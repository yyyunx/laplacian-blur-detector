import assert from "node:assert/strict";
import test from "node:test";
import { cellDescription, mountHeatmap, relativeColor, relativeScale, validLocalResult } from "../../web/heatmap.js";

const cell = (score, low = false) => ({ sharpness_score: score, is_low_texture: low });
test("relative mapping excludes low texture and handles zero, constant and unavailable ranges", () => {
  assert.deepEqual(relativeScale([cell(0), cell(10), cell(20), cell(1000, true)]), {
    minimum: 0, maximum: 20, values: [0, 0.5, 1, null],
  });
  assert.deepEqual(relativeScale([cell(0), cell(0)]).values, [0.5, 0.5]);
  assert.deepEqual(relativeScale([cell(0, true)]), { minimum: null, maximum: null, values: [null] });
  assert.deepEqual(relativeScale([]), { minimum: null, maximum: null, values: [] });
  assert.throws(() => relativeScale([cell(NaN)]));
  assert.throws(() => relativeScale([cell(-1)]));
  assert.deepEqual(relativeScale([cell(100), cell(110)]).values, [0, 1]);
  // Identical relative values can arise on completely different raw scales.
  assert.deepEqual(relativeScale([cell(0), cell(10)]).values, relativeScale([cell(0), cell(1e8)]).values);
});
test("color ramp has exact endpoints, a neutral midpoint and clamps", () => {
  assert.equal(relativeColor(0), "rgb(49, 54, 149)");
  assert.equal(relativeColor(0.5), "rgb(32, 178, 170)");
  assert.equal(relativeColor(1), "rgb(253, 231, 37)");
  assert.equal(relativeColor(-1), relativeColor(0));
  assert.equal(relativeColor(2), relativeColor(1));
});

function payload(metric = "laplacian") {
  return { success: true, metric, width: 64, height: 32, grid_rows: 1, grid_columns: 2,
    cells: [0, 1].map((column) => ({ row: 0, column, x: column * 32, y: 0, width: 32, height: 32,
      metric, sharpness_score: column * 100, texture_std: column * 20, is_low_texture: !column })) };
}
test("response validation checks geometry, metrics, sizes and finite measurements", () => {
  assert.ok(validLocalResult(payload()));
  for (const corrupt of [
    (p) => p.cells.pop(), (p) => { p.cells[0].x = 1; },
    (p) => { p.cells[0].sharpness_score = Infinity; }, (p) => { p.grid_rows = 33; },
    (p) => { p.cells[0].is_low_texture = "true"; }, (p) => { p.cells[0].metric = "tenengrad"; },
  ]) {
    const value = payload(); corrupt(value); assert.equal(validLocalResult(value), false);
  }
  assert.match(cellDescription(payload().cells[0]), /x 0, y 0.*32 × 32 px/);
  assert.match(cellDescription(payload().cells[0]), /insufficient evidence/);
  assert.doesNotMatch(cellDescription(payload().cells[0]), /blurry/i);
});

// Minimal DOM for controller behavior. Real SVG alignment is checked in-browser.
class Element {
  constructor() {
    this.attributes = new Map(); this.children = []; this.listeners = new Map(); this.style = {};
    this.value = ""; this.textContent = ""; this.disabled = false; this.hidden = false;
    this.classes = new Set();
    this.classList = { add: (v) => this.classes.add(v), remove: (v) => this.classes.delete(v) };
  }
  setAttribute(key, value) { this.attributes.set(key, String(value)); }
  getAttribute(key) { return this.attributes.get(key) ?? null; }
  toggleAttribute(key, on) { if (on) this.setAttribute(key, ""); else this.attributes.delete(key); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = [...children]; }
  addEventListener(name, listener) { this.listeners.set(name, [...(this.listeners.get(name) || []), listener]); }
  async fire(name, event = {}) {
    await Promise.all((this.listeners.get(name) || []).map((listener) => listener({ target: this, preventDefault() {}, ...event })));
  }
}
function setup(request = async () => ({ ok: true, json: async () => payload() })) {
  const elements = new Map();
  const doc = { getElementById(id) { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); }, createElementNS() { return new Element(); } };
  const get = (id) => doc.getElementById(id);
  for (const [id, value] of Object.entries({ "local-metric": "laplacian", "grid-rows": "1", "grid-columns": "2", "texture-cutoff": "5", "heatmap-opacity": "55" })) get(id).value = value;
  const widget = mountHeatmap(doc, request);
  return { widget, get, file: new File(["pixels"], "test.png", { type: "image/png" }) };
}
const tick = () => new Promise((resolve) => setImmediate(resolve));
const ok = (value = payload()) => ({ ok: true, json: async () => value });

test("UI draws hatching, hover and keyboard inspection; toggles and opacity are local", async () => {
  let requests = 0;
  const { widget, get, file } = setup(async (_url, options) => {
    requests++; assert.equal(options.body.get("metric"), "laplacian"); return ok();
  });
  assert.equal(get("view-heatmap").disabled, true);
  widget.setFile(file); await get("view-heatmap").fire("click");
  const overlay = get("heatmap-overlay");
  assert.equal(overlay.getAttribute("hidden"), null);
  assert.equal(overlay.getAttribute("viewBox"), "0 0 64 32");
  assert.equal(overlay.children[1].getAttribute("fill"), "url(#low-texture-hatch)");
  assert.match(get("heatmap-range").textContent, /midpoint color/);
  await overlay.fire("pointermove", { target: overlay.children[1] });
  assert.match(get("cell-information").textContent, /Low texture/);
  await overlay.fire("keydown", { key: "ArrowRight" });
  assert.match(get("cell-information").textContent, /x 32, y 0/);
  get("heatmap-opacity").value = "25";
  await get("heatmap-opacity").fire("input");
  assert.equal(overlay.style.opacity, "0.25");
  assert.equal(get("opacity-value").textContent, "25%");
  await get("view-original").fire("click"); assert.equal(overlay.getAttribute("hidden"), "");
  await get("view-heatmap").fire("click"); assert.equal(overlay.getAttribute("hidden"), null);
  assert.equal(requests, 1);
  widget.setFile(null);
  assert.equal(overlay.children.length, 0);
  assert.equal(get("view-heatmap").disabled, true);
});

test("metric changes refresh only the local endpoint and retain opacity", async () => {
  const metrics = [];
  const { widget, get, file } = setup(async (url, options) => {
    assert.equal(url, "/api/sharpness/local");
    const metric = options.body.get("metric"); metrics.push(metric); return ok(payload(metric));
  });
  widget.setFile(file); await get("view-heatmap").fire("click");
  get("local-metric").value = "tenengrad"; await get("local-metric").fire("change"); await tick();
  assert.deepEqual(metrics, ["laplacian", "tenengrad"]);
  assert.equal(get("view-heatmap").getAttribute("aria-pressed"), "true");
  assert.equal(get("heatmap-overlay").style.opacity, "0.55");
});

test("switching files discards an in-flight response even if fetch ignores abort", async () => {
  let resolve;
  const { widget, get, file } = setup(() => new Promise((done) => { resolve = done; }));
  widget.setFile(file); const pending = get("view-heatmap").fire("click");
  widget.setFile(new File(["new"], "other.png"));
  resolve(ok()); await pending;
  assert.equal(get("heatmap-overlay").children.length, 0);
  assert.equal(get("view-original").getAttribute("aria-pressed"), "true");
});

test("rapid metric changes ignore stale completions without clearing the current loading state", async () => {
  const resolve = {};
  const { widget, get, file } = setup((_url, options) => new Promise((done) => {
    resolve[options.body.get("metric")] = done;
  }));
  widget.setFile(file);
  const first = get("view-heatmap").fire("click");
  get("local-metric").value = "tenengrad";
  await get("local-metric").fire("change");
  resolve.laplacian(ok(payload("laplacian"))); await first;
  assert.equal(get("view-heatmap").disabled, true);
  assert.equal(get("heatmap-overlay").children.length, 0);
  resolve.tenengrad(ok(payload("tenengrad"))); await tick();
  assert.equal(get("view-heatmap").disabled, false);
  const overlay = get("heatmap-overlay");
  await overlay.fire("pointermove", { target: overlay.children[2] });
  assert.match(get("cell-information").textContent, /Tenengrad score/);
});

test("errors leave the original visible and allow retries; invalid inputs do not upload", async () => {
  let requests = 0;
  const { widget, get, file } = setup(async () => {
    requests++;
    return requests === 1 ? { ok: false, json: async () => ({ detail: "Choose a smaller grid." }) } : ok();
  });
  widget.setFile(file);
  get("grid-rows").value = "33"; await get("view-heatmap").fire("click"); assert.equal(requests, 0);
  get("grid-rows").value = "1"; await get("view-heatmap").fire("click");
  assert.match(get("heatmap-status").textContent, /Choose a smaller grid/);
  assert.equal(get("heatmap-overlay").getAttribute("hidden"), "");
  await get("view-heatmap").fire("click"); assert.equal(requests, 2);
  assert.equal(get("heatmap-overlay").getAttribute("hidden"), null);
});

test("batch work cancels pending local analysis and prevents competing uploads", async () => {
  let resolve, signal, requests = 0;
  const { widget, get, file } = setup((_url, options) => {
    requests++; signal = options.signal; return new Promise((done) => { resolve = done; });
  });
  widget.setFile(file); const pending = get("view-heatmap").fire("click");
  widget.setBatchBusy(true); assert.equal(signal.aborted, true);
  await get("view-heatmap").fire("click"); assert.equal(requests, 1);
  resolve(ok()); await pending;
  assert.equal(get("heatmap-overlay").children.length, 0);
  assert.equal(get("view-heatmap").disabled, true);
  widget.setBatchBusy(false); assert.equal(get("view-heatmap").disabled, false);
});
