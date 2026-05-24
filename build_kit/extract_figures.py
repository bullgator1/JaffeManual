#!/usr/bin/env python3
"""
extract_figures.py — pull substantive figures (with captions) from a Jaffe chapter
PDF slice into a figures/ folder + figures.json manifest.

Renders the figure's PAGE RECT to a pixmap (what the reader actually sees) instead
of extracting raw image xrefs — this avoids PyMuPDF soft-mask/stencil corruption on
the layered Lippincott illustrations.

Usage:
    python3 extract_figures.py "1 NEUROSURGERY.pdf" --section-id neurosurgery --out-dir figures
"""
import argparse, json, re, sys
from pathlib import Path
import fitz

MIN_W_PT = 90        # ignore narrow rules/icons (points)
MIN_H_PT = 70
ZOOM     = 1.6       # render at 2x for crispness, then JPEG
QUALITY  = 60
FIGCAP_RE = re.compile(r"Figure\s+\d+\.\d+-\d+\.?\s+[^\n]*(?:\n(?!Figure\s+\d|\s*$)[^\n]*){0,3}")

def book_page_of(page):
    """Detect the printed book page number from the running header (number leads
    on even pages, trails on odd) — mirrors ingest_chapter.py's logic."""
    lines = [l for l in page.get_text("text").split("\n") if l.strip()]
    for l in lines[:3] + lines[-3:]:
        m = re.match(r"^\s*(\d{1,4})\s+c\s*h\s*a\s*p\s*t\s*e\s*r\b", l, re.I)
        if m and 1 <= int(m.group(1)) <= 1400: return int(m.group(1))
        m = re.search(r"\b[A-Za-z].*?\s{2,}(\d{1,4})\s*$", l)
        if m and 1 <= int(m.group(1)) <= 1400 and len(l.strip()) < 90: return int(m.group(1))
        m = re.match(r"^(\d{1,4})$", l.strip())
        if m and 1 <= int(m.group(1)) <= 1400: return int(m.group(1))
    return None

def captions_on(page):
    txt = page.get_text("text")
    caps = []
    for m in FIGCAP_RE.finditer(txt):
        c = re.sub(r"\s+", " ", m.group(0)).strip()
        ref = re.match(r"(Figure\s+\d+\.\d+-\d+)", c)
        caps.append((ref.group(1) if ref else "", c[:400]))
    return caps

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--section-id", required=True)
    ap.add_argument("--out-dir", default="figures")
    args = ap.parse_args()

    src = Path(args.input)
    if not src.exists(): sys.exit(f"not found: {src}")
    out = Path(args.out_dir); out.mkdir(exist_ok=True)
    manifest_path = out / "figures.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    d = fitz.open(str(src))
    entries, seq = [], 0
    last_bp = None
    for pi, pg in enumerate(d):
        bp = book_page_of(pg)
        if bp: last_bp = bp
        elif last_bp is not None: last_bp = last_bp + 1
        caps = captions_on(pg)
        cap_i = 0
        # group image rects on the page; merge overlapping/adjacent into one figure
        rects = []
        for im in pg.get_images(full=True):
            for r in pg.get_image_rects(im[0]):
                if r.width >= MIN_W_PT and r.height >= MIN_H_PT:
                    rects.append(fitz.Rect(r))
        # merge rects that overlap or nearly touch (multi-image single figure)
        merged = []
        for r in sorted(rects, key=lambda r:(round(r.y0), round(r.x0))):
            placed = False
            for i,mr in enumerate(merged):
                if mr.intersects(r) or abs(mr.y1 - r.y0) < 24:
                    merged[i] = mr | r; placed = True; break
            if not placed: merged.append(+r)
        for r in merged:
            # pad slightly to include the whole illustration
            r = fitz.Rect(r.x0-4, r.y0-4, r.x1+4, r.y1+4) & pg.rect
            pix = pg.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=r)
            if pix.width < 60 or pix.height < 50:
                continue
            seq += 1
            fname = f"{args.section_id}_{seq:03d}.jpg"
            pix.pil_save(out / fname, format="JPEG", quality=QUALITY, optimize=True)
            ref, cap = (caps[cap_i] if cap_i < len(caps) else ("", ""))
            cap_i += 1
            entries.append({"file": fname, "caption": cap, "page": pi,
                            "bookPage": last_bp, "figref": ref})

    manifest[args.section_id] = entries
    manifest_path.write_text(json.dumps(manifest, indent=1))
    print(f"[done] {args.section_id}: {len(entries)} figures -> {out}/", file=sys.stderr)

if __name__ == "__main__":
    main()
