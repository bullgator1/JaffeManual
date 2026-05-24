# Anesthesia Procedure Reference — Project Instructions

This file is the **single source of truth** for the app's data schema and the
clinical-content quality bar. Both project skills read it first:
`ingest-jaffe-chapter` (PDF → `.txt`) and `add-procedure-to-app` (`.txt` →
entries in `index.html`).

## What this project is

A prep-focused anesthesia reference distilled from *Jaffe's Anesthesiologist's
Manual of Surgical Procedures, 5th ed. (Wolters Kluwer, 2014)*. The audience is
an anesthesiologist prepping a real case. Each entry answers: *what is the
surgeon doing, and what does it mean for my anesthetic?* — not a transcription of
the surgical chapter.

It is a **distillation**, not a reproduction. Figures are NOT embedded; they live
in the source PDF. (This is the deliberate difference from the Surgical Recall
project — see the build kit's README.)

## Pipeline (two steps)

1. **Ingest** a chapter PDF → page-marked, searchable `<N>_<CHAPTER>.txt`
   (skill `ingest-jaffe-chapter`, script `jaffe_build_kit/ingest_chapter.py`).
   These `.txt` files ARE the project knowledge.
2. **Distill** the `.txt` → data objects in the `PROCEDURES` array in `index.html`
   (skill `add-procedure-to-app`, validator `jaffe_build_kit/validate_app.js`).

## The PROCEDURES schema (authoritative — copy this shape exactly)

```js
{
  id: "kebab-case-unique",            // stable; URL hash + nav. NEVER reuse or rename.
  name: "Full Procedure Name",
  section: "Neurosurgery",            // Jaffe section name; groups the nav. Reuse the EXACT string across a chapter.
  page: "4",                          // book page (string). Ranges ok: "4–14".
  tags: ["GETA","Sitting","Burst-suppression"],  // short anesthetic descriptors
  snapshot: {                         // ALL SIX keys required; each value short (a few words)
    position:  "Supine, head pinned",
    time:      "3–6 h",
    ebl:       "200–500 mL",
    painScore: "4–6",
    anesthesia:"GETA",
    mortality: "Low–moderate"
  },
  flags: [                            // 2–4 can't-miss items; bold the danger noun/verb with **asterisks**
    "… **bold the dangerous thing** …"
  ],
  technique: {
    summary: "1–3 sentences: what the surgeon does, framed for anesthetic consequence.",
    steps: ["critical step that matters to us", "…"]   // 3–6 steps
  },
  physiology: ["what the procedure does to the patient", "…"],
  comorbid:   ["who presents + coexisting disease that shapes the plan", "…"],
  phases: {
    pre:   ["pre-operative concern", "…"],
    intra: ["intra-operative concern", "…"],
    post:  ["post-operative concern", "…"]
  },
  source: "Jaffe 5e (2014), Neurosurgery §1.1, p. 4–14; <any added articles, dated>."
}
```

Required top-level keys: `id, name, section, page, tags, snapshot, flags,
technique, physiology, comorbid, phases, source`.
Required `snapshot` keys: `position, time, ebl, painScore, anesthesia, mortality`.
Required `phases` keys: `pre, intra, post`.

Inline `**bold**` is the ONLY markup in strings (rendered by the `mdBold` helper).
No other markdown, no HTML in strings. Use plain unicode symbols (↑ ↓ → ° ≥ µ)
directly. Match the quoting convention of existing entries so a stray `'` doesn't
break a string.

## Content conventions (the clinical quality bar — non-negotiable)

- **Anesthetic relevance first.** Surgical detail only where it has anesthetic
  consequence (open globe → IOP; sitting craniotomy → venous air embolism; shared
  airway → blood in the field). Don't transcribe the chapter wholesale.
- **Flags are the lead** — the 2–4 things an attending says out loud first: the
  contraindication, the competing-priorities trap, the dangerous drug/technique
  interaction, "always verify the side." Bold the danger inline.
- **Preserve specific values verbatim**: doses, concentrations, time intervals,
  pressure/IOP thresholds, percentages, age cutoffs. Never round or vague them out
  — they are the point of the reference.
- **Distinguish edition/source.** Baseline is Jaffe 5e (2014). Anything from a
  newer edition or an article is attributed and dated in `source`, and flagged
  inline as an update (e.g. "(2022 ASRA update: …)"). NEVER silently overwrite
  2014 guidance.
- **No invented content.** If the chapter cross-references material not in the
  extract (e.g. "see Pediatric …, p. 1199"), say so rather than fabricating. Mark
  any number you're unsure of.
- **Combine related procedures** (standing preference for granular chapters).
  Procedures sharing an "Anesthetic Considerations" block and population become one
  denser entry; name it to list what it covers and enumerate the page range +
  covered procedures in `source`. The neurosurgery pass distills ~30 chapter
  procedures into ~14 entries. When in doubt, prefer fewer/denser.

## Figures (added 2026-05 — reverses the original text-only design)

The project originally embedded NO figures (figures-in-PDF only). This was
**reversed by user decision**: figures are now included because they're high-yield
(circle-of-Willis aneurysm frequencies, block anatomy, positioning diagrams).

How figures work:
- Extracted per chapter by `build_kit/extract_figures.py`, which **renders each
  figure's page rect to a JPEG** (NOT raw xref extraction — that corrupts the
  layered Lippincott illustrations) into a `figures/` folder, plus a
  `figures/figures.json` manifest keyed by section-id. Each manifest entry:
  `{file, caption, bookPage, figref}`.
- `build_kit/inject_figures.py` inlines the manifest into `index.html` as
  `window.__FIGURES__`. The renderer maps a figure to a procedure when the
  figure's **bookPage falls within the procedure's page range**.
- **ALL figures are included** (no curation/omission), shown **expanded inline by
  default** at the BOTTOM of each entry (after the anesthetic content, so the
  lead never gets pushed down). Click a figure for a lightbox.
- Figures are **base64-embedded directly into index.html** by `inject_figures.py`,
  making it a single self-contained file that works anywhere (opened standalone,
  shared, or served) — no `figures/` folder dependency at runtime. Measured 6
  chapters = ~4.5 MB of images → ~6.3 MB self-contained index.html; full book
  projects to ~13 MB, which is fine (Surgical Recall's was ~8 MB).
  (NOTE: this reverses an earlier interim decision to use a referenced /figures/
  folder — that broke images whenever index.html was opened without the folder
  beside it. Embedding is more robust.)
- The `figures/` folder is STILL kept in the repo as the durable image source
  (so a rebuild doesn't require re-extracting), but the SERVED index.html embeds
  them and does not read the folder.


- **Repo storage of figures:** figures are NOT committed to the repo (neither a loose folder nor a zip). They're base64-embedded in index.html (the served app) and regenerated from the full Jaffe PDF when needed. The PDF is the single source of truth for images. To rebuild/extend figures: run extract_figures.py against the PDF slice for the chapter (writes figures/), then inject_figures.py to embed into index.html. The figures/ folder is a transient build artifact, gitignored.

**index.html NEVER goes in project storage** — it's repo-only. Adding it to
project knowledge triggers "project knowledge exceeds maximum" and creates a
stale indexed copy. Project storage is ONLY for the chapter .txt extracts.

Per-chapter figure step (run alongside ingest/distill):
```bash
python3 build_kit/extract_figures.py "N CHAPTER.pdf" --section-id <sectionid> --out-dir figures
python3 build_kit/inject_figures.py index.html figures/figures.json figures
```
`inject_figures.py` base64-embeds the images INTO index.html (self-contained).
`<sectionid>` is the first token of the section name lowercased (e.g.
"neurosurgery", "ophthalmic", "thoracic", "cardiovascular") — must match what the
renderer's `sectionId()` derives from the entry's `section` field.

## Renderer (do NOT touch when only adding data)

`index.html` is a single self-contained file. The render functions — `mdBold`,
`renderNav`, `renderWelcome`, `renderProcedure`, `PILLARS`, `groupBySection`,
search/filter — are stable. **Adding a procedure = adding a data object to the
`PROCEDURES` array. Nothing else.** Only touch the renderer to deliberately add a
brand-new schema field, which must then be added here, rendered in
`renderProcedure`, and backfilled on every existing entry.

## Edition note

This project is built on the **5th edition (2014)**. The all-in-one 5e PDF is the
durable input (kept in the repo / dragged into chat).

**Verified (2026-05):** the per-chapter ProQuest PDFs (ISBN 9781451176605, the
files behind the original `.txt` extracts) are the **same 5th edition (2014)** as
the all-in-one PDF — not a different edition. A value-level diff of Chapter 1
(Neurosurgery) found **179 identical clinical values, zero differences**, with
matching prose (Hunt-Hess mortality figures, etc.). So the existing per-chapter
`.txt` extracts are reusable as 5e; they do not need re-ingestion for edition
reasons. Either source (all-in-one slice or per-chapter ProQuest PDF) yields an
equivalent extract — `ingest_chapter.py` handles both, and strips the ProQuest
watermark either way. The all-in-one PDF is the canonical durable input; treat
per-chapter PDFs as an equally-valid alternate.
