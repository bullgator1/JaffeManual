#!/usr/bin/env python3
"""
ingest_chapter.py — Jaffe chapter PDF/text -> page-marked, searchable .txt extract.

This is the repo-resident, runnable version of the logic described in the
`ingest-jaffe-chapter` skill. It exists so the ingest step can be run from a
clone of the repo without depending on the skill being loaded in a chat.

It branches on what `file -b` reports (NOT the .pdf extension), handles the four
known Jaffe container shapes, cleans the known artifacts (ProQuest watermark,
.indd build stamps, \\u0002 hyphenation), detects book page numbers, writes
`===== PAGE N =====` markers, and prepends the standard metadata header +
procedure index.

Usage:
    python3 ingest_chapter.py "1 NEUROSURGERY.pdf"
    python3 ingest_chapter.py "1 NEUROSURGERY.pdf" --out 1_NEUROSURGERY.txt
    python3 ingest_chapter.py "1 NEUROSURGERY.pdf" --section "1.0 Neurosurgery"

Output goes to ./<N>_<CHAPTER>.txt by default (derived from the input name).

Notes:
- For a true image-only scan (PDF document, but pdftotext returns nothing) this
  script will tell you to OCR first (the pdf-to-searchable-text skill), then
  re-run on the OCR'd text.
- Always spot-check the result (see the skill's Step 4): doses, IOP/pressure
  thresholds, time intervals, percentages and age ranges must survive intact.
"""
import argparse
import re
import subprocess
import sys
import unicodedata
import zipfile
from pathlib import Path

WM_RE = re.compile(
    r"Jaffe, Richard A\.\. Anesthesiologist's Manual of Surgical Procedures.*?All rights reserved\.\s*",
    re.DOTALL,
)
# ProQuest watermark appears as separate lines (not always one contiguous block).
# Strip each line-type independently so both the contiguous and the split layout
# are handled. These run line-by-line in clean_text.
WM_LINE_RES = [
    re.compile(r"^.*Jaffe, Richard A\.\..*ProQuest.*$", re.IGNORECASE),       # citation line
    re.compile(r"^\s*Created from .*?\bon\b.*$", re.IGNORECASE),               # "Created from ... on <date>."
    re.compile(r"^\s*Copyright\b.*All rights reserved\.?\s*$", re.IGNORECASE), # copyright line
]
INDD_RE = re.compile(r"Jaffe_\d+-ch[\d.]+\.indd.*", re.IGNORECASE)
PAGENO_RE = re.compile(r"^(\d{1,4})(?:\s+section\b.*)?$", re.IGNORECASE)

# Jaffe 5e running-header patterns (seen in `pdftotext -layout` output):
#   even page: "6      c h a p t e r 1.1   Intracranial Neurosurgery"  (number LEADS)
#   odd  page: "Craniotomy for Intracranial Aneurysms         7"        (number TRAILS)
# The "chapter" word is letter-spaced ("c h a p t e r") so match it loosely.
HDR_LEAD_RE = re.compile(r"^\s*(\d{1,4})\s+c\s*h\s*a\s*p\s*t\s*e\s*r\b", re.IGNORECASE)
HDR_TRAIL_RE = re.compile(r"\b([A-Za-z].*?)\s{2,}(\d{1,4})\s*$")


def clean_text(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = WM_RE.sub("\n", s)               # strip contiguous-block watermark (old plain-text layout)
    # strip split-layout watermark line-by-line (ProQuest per-chapter PDFs)
    kept = []
    for line in s.split("\n"):
        if INDD_RE.search(line):
            continue
        if any(rx.match(line) for rx in WM_LINE_RES):
            continue
        kept.append(line)
    s = "\n".join(kept)
    s = s.replace("\u00ad", "")          # soft hyphen
    s = re.sub(r"\u0002\s*\n?\s*", "", s)  # rejoin \u0002 hyphenation wraps
    s = "".join(c for c in s if c in "\n\t" or unicodedata.category(c)[0] != "C")
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def detect_book_page(raw_chunk: str):
    """Detect the book page number from the RAW page chunk (before clean_text).

    Handles two layouts:
      * Jaffe 5e running header — number embedded in a "chapter N.N" header line,
        leading on even pages / trailing on odd pages (uses the letter-spaced
        "c h a p t e r" cue).
      * Older watermarked-plain-text — page number as a standalone first/second line.
    Scans the first 3 and last 3 non-empty lines.
    """
    lines = [l for l in raw_chunk.split("\n") if l.strip()]
    candidates = lines[:3] + lines[-3:]
    for l in candidates:
        m = HDR_LEAD_RE.match(l)
        if m and 1 <= int(m.group(1)) <= 1400:
            return int(m.group(1))
        m = HDR_TRAIL_RE.search(l)
        # only trust a trailing number if the line also looks like a header
        # (short-ish, title-case words) rather than body prose ending in a number
        if m and 1 <= int(m.group(2)) <= 1400 and len(l.strip()) < 90:
            return int(m.group(2))
        m = PAGENO_RE.match(l.strip())
        if m and 1 <= int(m.group(1)) <= 1400:
            return int(m.group(1))
    return None


def sniff(path: Path) -> str:
    """Return one of: 'pdf_text', 'pdf_image', 'zip', 'plain'."""
    kind = subprocess.run(
        ["file", "-b", str(path)], capture_output=True, text=True
    ).stdout.strip()
    head = path.read_bytes()[:8]
    if head.startswith(b"PK"):
        return "zip"
    if head.startswith(b"%PDF"):
        # text-bearing or image-only?
        txt = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            capture_output=True, text=True,
        ).stdout
        return "pdf_text" if txt.strip() else "pdf_image"
    if kind.startswith("PDF"):
        return "pdf_text"
    return "plain"  # 'data' / 'ASCII text' — likely watermarked plain text


def pages_from_pdf_text(path: Path):
    raw = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        capture_output=True, text=True,
    ).stdout
    out, last = [], None
    for chunk in raw.split("\f"):
        seg = clean_text(chunk)
        if not seg:
            continue
        n = detect_book_page(chunk)
        last = n if n else (last + 1 if last else None)
        out.append((str(last) if last else "?", seg))
    return out


def pages_from_zip(path: Path):
    import json
    with zipfile.ZipFile(path) as z:
        manifest = json.load(z.open("manifest.json"))
        chunks = [
            z.open(p["text"]["path"]).read().decode("utf-8", "replace")
            for p in manifest["pages"]
        ]
    out, last = [], None
    for chunk in chunks:
        seg = clean_text(chunk)
        if not seg:
            continue
        n = detect_book_page(chunk)
        last = n if n else (last + 1 if last else None)
        out.append((str(last) if last else "?", seg))
    return out


def pages_from_plain(path: Path):
    raw = path.read_text(encoding="utf-8", errors="replace")
    out, last = [], None
    for chunk in WM_RE.split(raw):
        seg = clean_text(chunk)
        if not seg:
            continue
        n = detect_book_page(chunk)
        last = n if n else (last + 1 if last else None)
        out.append((str(last) if last else "?", seg))
    return out


def _is_title_line(s: str) -> bool:
    """True if the line looks like (part of) a procedure title rather than body
    prose, a running header, or boilerplate. Handles BOTH ALL-CAPS titles (e.g.
    Neurosurgery chapter) and Title-Case titles (e.g. Ophthalmic chapter:
    'Corneal Transplant', 'Cataract Extraction with Intraocular Lens Insertion')."""
    if not s or len(s) < 3:
        return False
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return False
    # titles are short headers, not sentences
    if len(s) > 70:
        return False
    if s.endswith((".", ":", ";", ",")):
        return False
    # must not be mid-sentence prose: reject if it contains lowercase function
    # words AND ends without a capital-ish word pattern — instead require that
    # every "significant" word starts uppercase (Title Case) OR the line is CAPS.
    words = [w for w in re.split(r"\s+", s) if w]
    if not words:
        return False
    small = {"of","for","and","the","with","to","in","or","a","an","on","via"}
    sig = [w for w in words if w.lower() not in small]
    if not sig:
        return False
    caps_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    title_case = all(w[0].isupper() for w in sig if w[0].isalpha())
    if not (caps_ratio >= 0.7 or title_case):
        return False
    # reject boilerplate / structural headers / running-header words
    if re.search(r"\b(SECTION|CHAPTER|SUMMARY OF PROCEDURE|SURGICAL CONSIDERATIONS|"
                 r"PATIENT POPULATION|ANESTHETIC CONSIDERATIONS|INTRAOPERATIVE|"
                 r"POSTOPERATIVE|PREOPERATIVE|Suggested Reading|References?|"
                 r"Neurosurgery|Ophthalmic|Surgery)\b", s, re.I):
        # allow these words only if they're clearly part of a longer title, not the whole line
        if len(sig) <= 2:
            return False
    # reject lines that are mostly digits / a running-header page line
    if re.match(r"^\s*\d+\b", s) and len(sig) <= 2:
        return False
    return True


def build_procedure_index(pages):
    """Reassemble the procedure title (ALL-CAPS or Title-Case) that sits
    immediately above each 'SURGICAL CONSIDERATIONS' block. Titles may wrap
    across 1-3 lines, so walk upward collecting contiguous title lines and join
    them. Stops at a blank line, a page-number/running-header line, or prose."""
    index = []
    for pageno, body in pages:
        if "SURGICAL CONSIDERATIONS" not in body:
            continue
        lines = body.split("\n")
        for i, ln in enumerate(lines):
            if "SURGICAL CONSIDERATIONS" not in ln:
                continue
            title_parts = []
            for j in range(i - 1, max(-1, i - 6), -1):
                cand = lines[j].strip()
                # strip stray Cochrane-citation prefix bleeding from prior page
                cand = re.sub(r"^\d{4};\s*\d+\(\d+\):CD\d+\.\s*", "", cand).strip()
                # strip a leading running-header page number ("151" in "Ectropion Repair      151")
                cand = re.sub(r"\s{2,}\d{1,4}\s*$", "", cand).strip()
                cand = re.sub(r"^\d{1,4}\s{2,}", "", cand).strip()
                if not cand:
                    if title_parts:   # blank line ends the title block
                        break
                    continue
                if _is_title_line(cand):
                    title_parts.insert(0, cand)
                else:
                    break
            if title_parts:
                title = " ".join(title_parts)
                title = re.sub(r"\s{2,}", " ", title).strip()
                index.append((title.title(), pageno))
            break
    # dedupe preserving order
    seen, uniq = set(), []
    for name, pg in index:
        key = name.lower()
        if key not in seen:
            seen.add(key)
            uniq.append((name, pg))
    return uniq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="chapter file (often a .pdf extension regardless of real type)")
    ap.add_argument("--out", help="output .txt path (default derived from input)")
    ap.add_argument("--section", help="section label for header, e.g. '1.0 Neurosurgery'")
    args = ap.parse_args()

    src = Path(args.input)
    if not src.exists():
        sys.exit(f"not found: {src}")

    kind = sniff(src)
    print(f"[sniff] {src.name} -> {kind}", file=sys.stderr)
    if kind == "pdf_image":
        sys.exit(
            "Image-only PDF (pdftotext empty). OCR first via the "
            "pdf-to-searchable-text skill, then re-run on the OCR'd text."
        )
    pages = {
        "pdf_text": pages_from_pdf_text,
        "zip": pages_from_zip,
        "plain": pages_from_plain,
    }[kind](src)

    if not pages:
        sys.exit("no pages parsed — inspect the file by hand")

    # derive chapter number + UPPER_SNAKE name from the input filename
    stem = re.sub(r"\.[^.]+$", "", src.name)
    m = re.match(r"\s*(\d+)\s*[_\- ]+(.+)$", stem)
    num = m.group(1) if m else "X"
    name = (m.group(2) if m else stem).strip().upper()
    name = re.sub(r"[^A-Z0-9]+", "_", name).strip("_")
    out = Path(args.out) if args.out else Path(f"{num}_{name}.txt")

    first_pg = next((p for p, _ in pages if p != "?"), "?")
    last_pg = next((p for p, _ in reversed(pages) if p != "?"), "?")
    section = args.section or f"{num}.0 {name.replace('_', ' ').title()}"

    proc_index = build_procedure_index(pages)

    with open(out, "w", encoding="utf-8") as fh:
        fh.write(f"# {num}_{name}\n")
        fh.write(
            f"# Source: {src.name} (Jaffe's Anesthesiologist's Manual of "
            f"Surgical Procedures, 5th ed., Wolters Kluwer, 2014)\n"
        )
        fh.write(f"# Section: {section}\n")
        fh.write(f"# Pages: {first_pg}-{last_pg}\n")
        fh.write("# Note: Text-extract for project knowledge. Figures live in the source PDF only.\n\n")
        fh.write("===== PROCEDURE INDEX =====\n")
        if proc_index:
            for nm, pg in proc_index:
                fh.write(f"- {nm} (p. {pg})\n")
        else:
            fh.write("- (none auto-detected; add by hand after review)\n")
        fh.write("\n")
        for pageno, body in pages:
            fh.write(f"===== PAGE {pageno} =====\n{body}\n\n")

    # quick sanity: \u0002 must be gone
    leftover = out.read_text(encoding="utf-8").count("\u0002")
    print(f"[done] {out}  pages={len(pages)}  procedures={len(proc_index)}  "
          f"\\u0002_leftover={leftover}", file=sys.stderr)
    if leftover:
        print("[warn] \\u0002 control chars remain — hyphenation rejoin incomplete", file=sys.stderr)


if __name__ == "__main__":
    main()
