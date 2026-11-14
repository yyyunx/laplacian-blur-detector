import assert from "node:assert/strict";
import test from "node:test";
import { resultStatus, resultsCsv, sortResults } from "../../web/batch-utils.js";

const item = (id, name, status, score, blurry = false) => ({
  id, file: { name, size: 123 }, status,
  result: status === "done" ? { blur_score: score, threshold: 100, width: 10, height: 20, is_blurry: blurry, message: "Checked" } : null,
  error: status === "error" ? "Invalid image" : "",
});

test("sorting keeps unfinished/failed items last in either score direction", () => {
  const rows = [item(0, "pending.png", "pending"), item(1, "low.png", "done", 0, true), item(2, "failed.png", "error"), item(3, "high.png", "done", 1000)];
  assert.deepEqual(sortResults(rows, "score-asc").map((row) => row.id), [1, 3, 0, 2]);
  assert.deepEqual(sortResults(rows, "score-desc").map((row) => row.id), [3, 1, 0, 2]);
  assert.deepEqual(rows.map((row) => row.id), [0, 1, 2, 3]);
});

test("zero scores and threshold boundaries retain their actual status", () => {
  assert.equal(resultStatus(item(0, "zero.png", "done", 0, true)), "blurry");
  assert.equal(resultStatus(item(1, "edge.png", "done", 100)), "clear");
  assert.match(resultsCsv([item(0, "zero.png", "done", 0, true)]), /"0","100"/);
});

test("CSV quotes filenames, newlines, and commas without interpreting formulas", () => {
  const formula = item(0, '=HYPERLINK("bad").png', "error");
  formula.error = "bad, file\nretry";
  const csv = resultsCsv([formula, item(1, "normal.png", "pending")]);
  assert.ok(csv.includes('"\'=HYPERLINK(""bad"").png"'));
  assert.ok(csv.includes('"bad, file\nretry"'));
  assert.ok(csv.includes('"normal.png","pending","",""'));
});

test("CSV includes failures and pending items with empty numeric fields", () => {
  const csv = resultsCsv([item(0, "bad.png", "error"), item(1, "later.png", "pending")]);
  assert.ok(csv.includes('"bad.png","error","","","","","123","Invalid image"'));
  assert.ok(csv.includes('"later.png","pending","","","","","123",""'));
});
