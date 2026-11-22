import assert from "node:assert/strict";
import test from "node:test";
import { exampleDiagnosticPolicy, mountQualityDiagnostics, validQualityResult } from "../../web/quality-diagnostics.js";

function payload() {
  return {
    success: true, schema_version: 1, width: 16, height: 16, policy: {}, limitations: ["Not an acceptance decision."],
    measurements: {
      brightness: { mean: 0.1, median: 0.1 },
      exposure: { dark_pixel_ratio: 1, bright_pixel_ratio: 0, dark_pixel_cutoff: 16 / 255, bright_pixel_cutoff: 250 / 255 },
      resolution: { width: 16, height: 16, pixels: 256 },
      sharpness: { laplacian_score: 0, tenengrad_score: 0, texture_std: 0, texture_std_normalized: 0, is_low_texture: true, input_intensity_max: 255 },
    },
    checks: Object.fromEntries(["brightness", "underexposure", "overexposure", "resolution", "sharpness", "texture"].map((name) => [name, {
      status: name === "sharpness" || name === "texture" ? "insufficient_evidence" : "not_evaluated",
      message: name === "sharpness" ? "Low texture; insufficient evidence." : "Measured.",
      suggestion: name === "sharpness" ? "Inspect a textured subject region." : null,
      limitation: "Content can affect this measurement.",
    }])),
  };
}
class Element {
  constructor() { this.children = []; this.listeners = new Map(); this.value = ""; this.textContent = ""; this.disabled = false; this.hidden = false; this.attributes = new Map(); }
  setAttribute(k, v) { this.attributes.set(k, v); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  addEventListener(name, listener) { this.listeners.set(name, listener); }
  async fire(name) { await this.listeners.get(name)?.({ target: this }); }
}
function setup(request = async () => ({ ok: true, json: async () => payload() })) {
  const elements = new Map();
  const get = (id) => { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); };
  get("quality-policy").value = "{}";
  const widget = mountQualityDiagnostics({ getElementById: get, createElement: () => new Element() }, request);
  return { widget, get, file: new File(["synthetic"], "demo.png", { type: "image/png" }) };
}
const ok = (value = payload()) => ({ ok: true, json: async () => value });
const tick = () => new Promise((resolve) => setImmediate(resolve));
const text = (element) => element.textContent + element.children.map(text).join(" ");

test("validates diagnostic numbers, statuses and geometry before rendering", () => {
  assert.ok(validQualityResult(payload()));
  for (const mutate of [
    (p) => { p.measurements.brightness.mean = NaN; },
    (p) => { p.measurements.exposure.dark_pixel_ratio = 2; },
    (p) => { p.measurements.resolution.pixels = 257; },
    (p) => { p.measurements.sharpness.is_low_texture = "true"; },
    (p) => { p.checks.texture.status = "pass"; },
  ]) { const p = payload(); mutate(p); assert.equal(validQualityResult(p), false); }
});

test("renders measurements, evidence and suggestions without making a quality gate", async () => {
  const { widget, get, file } = setup();
  assert.equal(get("quality-run").disabled, true);
  widget.setFile(file); await get("quality-run").fire("click");
  assert.equal(get("quality-results").hidden, false);
  assert.match(text(get("quality-metrics")), /Mean brightness.*0.100/);
  assert.match(text(get("quality-warnings")), /insufficient evidence/);
  assert.match(text(get("quality-suggestions")), /textured subject/);
  assert.match(get("quality-summary").textContent, /0 configured warning/);
  assert.doesNotMatch(text(get("quality-warnings")), /blurry|rejected/i);
});

test("example and measurements-only policies are explicit, editable and do not auto-upload", async () => {
  let requests = 0;
  const { widget, get, file } = setup(async (url, options) => {
    assert.equal(url, "/api/quality/diagnose"); requests++;
    assert.deepEqual(JSON.parse(options.body.get("policy")), exampleDiagnosticPolicy());
    return ok();
  });
  widget.setFile(file); await get("quality-example").fire("click");
  assert.equal(requests, 0); assert.match(get("quality-status").textContent, /Uncalibrated/);
  await get("quality-run").fire("click"); assert.equal(requests, 1);
  await get("quality-reset").fire("click");
  assert.equal(get("quality-policy").value, "{}"); assert.equal(get("quality-results").hidden, true);
});

test("small nonzero normalized measurements are not displayed as zero", async () => {
  const p = payload(); p.measurements.brightness.mean = 1 / 65535;
  p.measurements.exposure.bright_pixel_ratio = 1e-7;
  const { widget, get, file } = setup(async () => ok(p));
  widget.setFile(file); await get("quality-run").fire("click");
  assert.match(text(get("quality-metrics")), /Mean brightness.*1.53e-5/);
  assert.match(text(get("quality-metrics")), /1.00e-5%/);
});

test("malformed or oversized policy never uploads; raw valid JSON reaches strict server validation", async () => {
  let calls = 0;
  const raw = '{"min_width":1,"min_width":2,"min_tenengrad_score":1e400}';
  const { widget, get, file } = setup(async (_url, options) => {
    calls++; assert.equal(options.body.get("policy"), raw);
    return { ok: false, json: async () => ({ detail: "Duplicate policy fields are not allowed." }) };
  });
  widget.setFile(file);
  for (const invalid of ["{", "[]", " ".repeat(2) + '{"x":"' + "x".repeat(8192) + '"}']) {
    get("quality-policy").value = invalid; await get("quality-run").fire("click");
    assert.equal(calls, 0);
  }
  get("quality-policy").value = raw; await get("quality-run").fire("click");
  assert.equal(calls, 1); assert.match(get("quality-status").textContent, /Duplicate policy/);
});

test("switching images ignores stale completions even when fetch ignores abort", async () => {
  let resolve;
  const { widget, get, file } = setup(() => new Promise((done) => { resolve = done; }));
  widget.setFile(file); const pending = get("quality-run").fire("click");
  widget.setFile(new File(["next"], "other.png")); resolve(ok()); await pending;
  assert.equal(get("quality-results").hidden, true);
  assert.equal(get("quality-run").disabled, false);
});

test("editing policy invalidates old results and pending work without repainting stale hints", async () => {
  const resolvers = [];
  const { widget, get, file } = setup(() => new Promise((done) => { resolvers.push(done); }));
  widget.setFile(file); const first = get("quality-run").fire("click");
  get("quality-policy").value = '{"min_width":1024}'; await get("quality-policy").fire("input");
  const second = get("quality-run").fire("click");
  resolvers[0](ok()); await first;
  assert.equal(get("quality-run").disabled, true); assert.equal(get("quality-results").hidden, true);
  const updated = payload(); updated.checks.resolution = { status: "warning", message: "Too small for configured width.", suggestion: "Capture at higher resolution.", limitation: "No useful detail guarantee." };
  resolvers[1](ok(updated)); await second;
  assert.match(text(get("quality-warnings")), /Too small/);
  assert.match(text(get("quality-suggestions")), /higher resolution/);
});

test("batch activity aborts pending diagnostics; errors allow retry and clear removes results", async () => {
  let resolve, signal;
  const { widget, get, file } = setup((_url, options) => {
    signal = options.signal; return new Promise((done) => { resolve = done; });
  });
  widget.setFile(file); const pending = get("quality-run").fire("click");
  widget.setBatchBusy(true); assert.equal(signal.aborted, true);
  resolve(ok()); await pending;
  assert.equal(get("quality-results").hidden, true); assert.equal(get("quality-run").disabled, true);
  widget.setBatchBusy(false); const retry = get("quality-run").fire("click");
  resolve({ ok: false, json: async () => ({ detail: "Service is busy." }) }); await retry;
  assert.match(get("quality-status").textContent, /Service is busy/); assert.equal(get("quality-run").disabled, false);
  const last = get("quality-run").fire("click"); resolve(ok()); await last;
  widget.setFile(null); assert.equal(get("quality-results").hidden, true); assert.equal(get("quality-run").disabled, true);
  await tick();
});
