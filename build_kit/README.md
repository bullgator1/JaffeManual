# Anesthesia Procedure Reference — Maintenance & Build Kit

This kit makes the **Anesthesia Procedure Reference** app rebuildable and
updatable without depending on a chat session, a temporary sandbox, or
project-knowledge being loaded. Commit it to the repo alongside the durable
inputs below.

> **This is NOT a Surgical Recall–style full-book reproduction.** Read
> "How this project differs from Surgical Recall" before assuming it works the
> same way. The short version: Surgical Recall's app is a *scripted,
> figure-faithful reproduction of the entire book*; this app is a
> *hand-distilled clinical reference* where each procedure is boiled down to
> flags/phases/snapshot by judgment, and figures stay in the source PDF. The
> distillation is human work and is **not** regenerable by a script.

## The durable set (keep these in the repo)

Repo layout:

```
/                         repo root (GitHub Pages serves index.html here)
├── index.html            the app (build OUTPUT)
├── Anesthesiologist's…pdf the full 5e PDF (build INPUT; ~150 MB binary)  ← add this
├── build_kit/
│   ├── ingest_chapter.py   PDF/chapter → page-marked .txt
│   ├── validate_app.js     structural validator for index.html
│   ├── project_instructions.md  authoritative schema + quality bar
│   └── README.md           this file
└── extracts/
    ├── 1_NEUROSURGERY.txt        ✓ done (10 app entries)
    ├── 2_OPHTHALMIC_SURGERY.txt  ✓ done (6 app entries)
    └── …one .txt per chapter as ingested
```

1. **The full Jaffe 5e PDF** (~150 MB, 1,717 pp) — the build INPUT for new
   chapters. GitHub stores it as a plain binary, untouched. **Do NOT add it to
   project knowledge** (that strips images / re-encodes to text-only). Standing
   workflow: chapters are sliced from this full PDF — no per-chapter uploads.
2. **`build_kit/`** — the scripts + schema + this README.
3. **`index.html`** — the build OUTPUT, served by GitHub Pages.
4. **`extracts/*.txt`** — one per ingested chapter. These ARE the project
   knowledge; the app entries are distilled from them. Safe to also add to
   project storage for in-chat search (txt isn't degraded by indexing). The repo
   copy is canonical.

## How this project differs from Surgical Recall

| | Surgical Recall | Anesthesia Procedure Reference (Jaffe) |
|---|---|---|
| App goal | Reproduce the *whole book* | *Distill* procedures into a prep-focused reference |
| Figures | All 349 embedded as base64 | Left in the source PDF (anatomical line-drawings; prose carries the decisions) |
| Build | 7-script PDF→HTML pipeline, fully automatic | 2-step human-in-the-loop: extract text, then hand-distill |
| Regenerable from PDF? | Yes — Q&A is scriptable | **No** — distillation is judgment, not extraction |
| Per-chapter unit | Q&A pairs | One curated entry per procedure (often several procedures combined) |

Because the distillation can't be scripted, the "durable input" idea from the
Surgical Recall README still applies (keep the real PDF + tooling in the repo),
but the "run one script and get the whole app back" idea does **not**. What's
durable here is: the PDF, the `.txt` extracts, the curated `index.html`, the
schema in `project_instructions.md`, and the two skills + scripts that drive the
workflow.

## The workflow (two steps, one per skill)

Adding or updating a chapter is always these two steps, in order:

### Step 1 — Ingest the chapter PDF → searchable `.txt`
Skill: **`ingest-jaffe-chapter`**. Script: **`ingest_chapter.py`**.

```bash
pip install pymupdf --break-system-packages       # for figure/structure inspection
# poppler's pdftotext must be present: apt-get install poppler-utils

python3 ingest_chapter.py "1 NEUROSURGERY.pdf"
# -> writes 1_NEUROSURGERY.txt with a metadata header, a PROCEDURE INDEX,
#    and ===== PAGE N ===== markers using BOOK page numbers.
```

The script branches on what `file -b` reports (never the `.pdf` extension):
text-bearing PDF, zip-of-JPEG bundle, image-only scan (→ OCR first via
`pdf-to-searchable-text`), or watermarked plain-text masquerading as PDF. It
strips the ProQuest watermark and `.indd` stamps, rejoins `\u0002` hyphenation,
and detects book page numbers (line 1 on odd pages, line 2 on even pages).

**Always spot-check the output** (skill Step 4): doses, IOP/pressure thresholds,
time intervals, percentages, and age ranges must survive verbatim — they are the
whole point of the reference.

### Step 2 — Distill the `.txt` → entries in `index.html`
Skill: **`add-procedure-to-app`**. Validator: **`validate_app.js`**.

Read `project_instructions.md` first for the schema and quality bar, then work
through the `.txt` procedure by procedure, filling the PROCEDURES schema
(`flags`, `snapshot`, `technique`, `physiology`, `comorbid`, `phases`, `source`).
Closely-related procedures that share an "Anesthetic Considerations" block get
**combined** into one denser entry (the standing preference). Append the data
objects before the array's closing `];`, then validate:

```bash
node validate_app.js index.html
# checks required keys, the 6 snapshot keys, the 3 phase keys,
# non-empty flags, and unique ids. Exit 0 = PASS.
```

Then screenshot one new entry (playwright + chromium) to confirm it renders, and
commit `index.html` + the new `.txt`.

## Cold rebuild (from a fresh clone, no chat, no project knowledge)

1. `git clone` the repo.
2. Ensure the real Jaffe PDF is present (it's committed here; if it was kept out
   for size, drag it into a chat or place it in the clone).
3. For each chapter not yet in `index.html`: run `ingest_chapter.py` on its PDF
   slice (or the whole book, ingesting chapter ranges), then hand-distill into
   `index.html` per `add-procedure-to-app`, validating with `validate_app.js`.

There is no single "rebuild everything" button — and that's intentional. The
clinical distillation is the value, and it's reviewed by a human each time.

## Keep-or-delete the source PDF, per chapter

Default for Jaffe chapters: **delete the per-chapter PDF after extraction** — the
`.txt` carries the prose, summary tables, and population data. **Keep** a chapter
PDF (move to `/pdfs/` and note in `project_instructions.md`) only when a figure is
a decision algorithm / dosing chart / scoring matrix with no prose equivalent, or
a clinically-important table scrambled in extraction. The **full** book PDF stays
committed regardless — it's the durable input for future chapters.

## Provenance

Source: *Anesthesiologist's Manual of Surgical Procedures*, 5th Edition,
Richard A. Jaffe, MD, PhD, ed., Wolters Kluwer, 2014. This project distills the
book's anesthetic guidance for personal clinical-prep use; all rights remain with
the copyright holder. Figures are not reproduced; they remain in the source PDF.
