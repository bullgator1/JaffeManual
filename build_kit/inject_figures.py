#!/usr/bin/env python3
"""
inject_figures.py — inline figures into index.html as window.__FIGURES__,
EMBEDDING each image as a base64 data URI so index.html is fully self-contained
(works when opened standalone — no figures/ folder dependency).

Usage:
    python3 inject_figures.py index.html figures/figures.json [figures_dir]

Idempotent: replaces any prior __FIGURES__ injection. The figures/ folder is still
kept in the repo as the durable source, but the served index.html no longer needs it.
"""
import base64, json, re, sys, pathlib

html_path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")
man_path  = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "figures/figures.json")
fig_dir   = pathlib.Path(sys.argv[3] if len(sys.argv) > 3 else man_path.parent)

manifest = json.load(open(man_path))
slim = {}
embedded = 0
for sid, figs in manifest.items():
    out = []
    for e in figs:
        rec = {k: e.get(k) for k in ("caption", "bookPage", "figref")}
        img = fig_dir / e["file"]
        if img.exists():
            b = img.read_bytes()
            rec["data"] = "data:image/jpeg;base64," + base64.b64encode(b).decode()
            embedded += 1
        else:
            rec["data"] = ""   # missing image -> renderer skips
        out.append(rec)
    slim[sid] = out

inject = "window.__FIGURES__ = " + json.dumps(slim, separators=(",", ":")) + ";\n"
html = html_path.read_text()
html = re.sub(r"window\.__FIGURES__ = .*?;\n", "", html, flags=re.DOTALL)
html = html.replace("const PROCEDURES = [", inject + "const PROCEDURES = [", 1)
html_path.write_text(html)
mb = len(inject) / 1024 / 1024
print(f"embedded {embedded} figures across {len(slim)} section(s); "
      f"index.html figure payload ~{mb:.1f} MB")
