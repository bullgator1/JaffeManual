#!/usr/bin/env node
/*
 * validate_app.js — structural validator for the PROCEDURES array in index.html.
 *
 * Repo-resident version of the check described in the `add-procedure-to-app`
 * skill (Step 4). Evals the array, verifies every required key, the six snapshot
 * keys, the three phase keys, non-empty flags, and unique ids. Run it after any
 * edit to the data array, before committing.
 *
 * Usage:
 *     node validate_app.js [path/to/index.html]   # defaults to ./index.html
 *
 * Exit code 0 = PASS, 1 = FAIL (so it can gate a commit hook if you want).
 */
const fs = require("fs");

const path = process.argv[2] || "index.html";
if (!fs.existsSync(path)) {
  console.error(`not found: ${path}`);
  process.exit(1);
}
const html = fs.readFileSync(path, "utf8");
const m = html.match(/const PROCEDURES = (\[[\s\S]*?\n\];)/);
if (!m) {
  console.log("NO MATCH — array anchors broken (const PROCEDURES = [ ... \\n];)");
  process.exit(1);
}

let P;
try {
  P = eval(m[1]);
} catch (e) {
  console.log("EVAL ERROR — JS syntax problem in the array:");
  console.log("  " + e.message);
  process.exit(1);
}

const req = ["id", "name", "section", "page", "tags", "snapshot",
             "flags", "technique", "physiology", "comorbid", "phases", "source"];
const snap = ["position", "time", "ebl", "painScore", "anesthesia", "mortality"];
const ph = ["pre", "intra", "post"];

let ok = true;
const ids = new Set();
for (const p of P) {
  for (const k of req) if (!(k in p)) { console.log("MISSING", k, "in", p.id || p.name); ok = false; }
  for (const k of snap) if (!p.snapshot || !(k in p.snapshot)) { console.log("MISSING snapshot." + k, "in", p.id); ok = false; }
  for (const k of ph) if (!p.phases || !(k in p.phases)) { console.log("MISSING phases." + k, "in", p.id); ok = false; }
  if (!Array.isArray(p.flags) || p.flags.length < 1) { console.log("flags empty in", p.id); ok = false; }
  if (ids.has(p.id)) { console.log("DUP id", p.id); ok = false; }
  ids.add(p.id);
}
console.log("count", P.length, "| sections:", [...new Set(P.map(p => p.section))].join(" | "));
console.log(ok ? "VALIDATION PASS" : "VALIDATION FAIL");
process.exit(ok ? 0 : 1);
