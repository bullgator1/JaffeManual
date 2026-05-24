# Anesthesia Procedure Reference — Autopilot Build: Review Notes & Punch-List

**Status:** Complete draft of the entire procedural book. 86 entries, 15 sections, 374 figures embedded, self-contained `index.html` (~12 MB). App validates with no errors. **This is a draft to review — clinical content needs your end-check before you rely on it.**

## What got built while you were away (Chapters 7–15)
- **Ch7 General Surgery** — 74 source procedures → 9 grouped entries
- **Ch8 Obstetric/Gynecologic** — 29 → 4
- **Ch9 Urology** — 13 → 3
- **Ch10 Orthopedic** — 61 → 7
- **Ch11 Plastic/Reconstructive** — 15 → 5
- **Ch12 Pediatric** — 82 → 8 (the biggest chapter)
- **Ch13 Out-of-OR/Radiology** — 4
- **Ch14 Office-Based** — 2
- **Ch15 Emergency Procedures** — 2 (cricothyrotomy; pericardiocentesis + IO access)

## ⚠️ THINGS TO EYEBALL (in rough priority order)

1. **I almost missed Chapters 15 & 16.** My original boundary map had 14 chapters; your screenshot caught that the book has 16 sections. My Ch14 slice was also wrong — it ran 1594–1716 and swallowed Emergency + Appendices. **Fixed:** Ch14 re-cut to its true 10-page range (1594–1603), its contaminated figures purged and re-extracted (16 → correct 2 figures), page ranges corrected to 1563–1572. Worth a sanity-check that the Office-Based entries read correctly.

2. **Chapter 16 (Appendices) was deliberately NOT added.** It's reference tables/protocols — drug infusion rates, standard anesthetic protocols, pediatric epidural/spinal dosing, NMB monitoring — not surgical procedures. Forcing it into the per-procedure schema would distort the data model and search. **Your call:** if you want it, it belongs as a separate "Reference/Protocols" tab in a different format, which is a design decision I left to you rather than make unilaterally.

3. **Heavy combining in the big chapters.** Ch7 (74→9), Ch10 (61→7), Ch12 (82→8) compress a LOT. I grouped by shared anesthetic considerations, but please verify nothing clinically critical got lost — especially any niche procedure with unique flags that may have been folded into a broader entry.

4. **Figure book-page detection failed for Ch13 AND Ch15** (their running-header/caption format differs from the rest of the book). Both came back with all `bookPage: None`, so figures initially orphaned. **Fixed** with a slice-position fallback (estimating book page from PDF position). Mapping now: Ch13 principles 2 / cardioversion 2 / interventional 5 (ECT shows 0 — accurate, its figures landed at chapter start and were claimed by the principles entry); Ch15 cricothyrotomy 4 / pericardiocentesis-IO 6. The estimated page ranges are approximate — worth confirming the right figures sit with the right entries.

5. **Image quality was dialed down mid-run.** At Ch10 the embedded payload hit 14.9 MB and was trending toward ~20+ MB (sluggish, GitHub-unfriendly). I re-encoded ALL figures leaner (zoom 1.6, JPEG quality 60) → full book now ~12 MB. I spot-checked legibility (circle of Willis etc.) and labels remain readable, but if any specific diagram looks too soft, it can be re-extracted at higher quality for that chapter.

6. **Clinical doses/flags need your review throughout.** Every entry was distilled from the source + standard anesthesia knowledge, but specific numbers (drug doses, tourniquet pressures, spinal doses, etc.) should get a clinician's eye before clinical reliance. A few I'd check first: bariatric weight-based dosing (Ch7), C-section neuraxial doses (Ch8), TURP/cricothyrotomy specifics (Ch9/Ch15), pediatric cardiac shunt management (Ch12).

7. **Deduped carotid entry (from earlier sessions):** `carotid-endarterectomy-neuro` covers both the Neurosurgery and Cardiovascular listings; its source line notes both chapters. Intentional — just so you know why there isn't a separate CV carotid entry.

## File destinations (unchanged from our convention)
- **git repo** = `git_repo_files.zip` → self-contained index.html + build_kit/ + extracts/ + .gitignore. NO figures committed (they're embedded in index.html; loose folder trips GitHub's 100-file web-upload limit). You add the full PDF yourself.
- **project storage** = `project_storage_txts.zip` → ONLY the 15 .txt extracts (for future-chat search). index.html does NOT go in project storage (exceeds the knowledge-size limit).
- **standalone** = `index.html` → drop straight into GitHub Pages / open anywhere.
- **optional** = `figures_backup_optional.zip` → the loose figure JPEGs for your laptop (NOT for the repo).

---

## Autopilot run notes — Chapters 7–14 (2026-05-24)

**Status:** App now covers all 14 surgical chapters + Emergency Procedures = 86 entries, 15 sections, 374 figures embedded, ~11 MB self-contained index.html. Validates clean.

### Things to review (priority order)

1. **Ch14 boundary was originally wrong — now fixed.** The first Ch14 slice ran p1594–1716 and swallowed all of Chapter 15 (Emergency) AND Chapter 16 (Appendices), contaminating its text extract and figures. Corrected: Ch14 is truly only p1594–1603 (~10 pages, office-based principles + dental/laser). The 2 Office-Based entries are content-correct; figures re-extracted clean (2 genuine office figures).

2. **Heavy procedure-combining in the large chapters** — highest chance of a dropped nuance, please spot-check:
   - Ch7 General Surgery: 74 source procedures → 9 entries
   - Ch12 Pediatric: 82 → 8 entries
   - Ch10 Orthopedic: 61 → 7 entries
   - Ch8 OB/Gyn: 29 → 4; Ch11 Plastic: 15 → 5; Ch9 Urology: 13 → 3.

3. **Ch13 (Out-of-OR) figure mapping is approximate.** That chapter's running-header format broke automatic book-page detection (all figures came back with no page). Worked around by estimating page from PDF-slice position and widening the interventional-radiology entry's range to 1500–1560. Figures map (principles 2, cardioversion 2, interventional 5); ECT shows 0 (its figures landed at chapter start, claimed by the principles entry). Double-check these land on sensible entries.

4. **Figure encoding was dialed down mid-run** (at Ch10) to ZOOM 1.6 / QUALITY 60 after the payload hit ~15 MB. All chapters re-extracted at the leaner setting; full book is ~11 MB. Spot-checked legibility (circle of Willis etc.) — fine for reference. Re-raise quality in extract_figures.py if any figure is too soft.

5. **Clinical end-review still needed.** Every entry's flags/snapshot/doses are distilled and were self-validated structurally + screenshotted, but NOT clinically verified by a second human. Treat as a high-quality draft, not a final clinical authority.

6. **Chapter 16 (Appendices) — DONE & ENRICHED.** The appendices have a lot of high-yield, concrete anesthesia reference content; distilled into 4 entries in a "Reference (Appendices)" section with actual values:
   - **Standard Adult Anesthetic** (App A–C): induction/relaxant doses (propofol 1.5–2.5, etomidate 0.2–0.4, fentanyl 1–3 mcg/kg, roc 0.6/1.2 RSI), the RSI sequence (preox to ETO2>90%, cricoid 8–10 lb), lung-protective ventilation, VTE prophylaxis, indication-based preop testing.
   - **Standard Pediatric Anesthetic** (App D): NPO 2-4-6-8 rule, ETT (age/4)+4 sizing, weight-based premed (midazolam 0.5–0.75 mg/kg max 20mg) and induction doses.
   - **Pediatric Pain & Regional** (App E): PCA, caudal/epidural dosing framework.
   - **Preop Meds + Neuraxial Anticoagulation + Latex** (App F–H): hold/continue meds, herbals, the safety-critical neuraxial-anticoagulation timing table (flagged to verify against current ASRA), latex precautions.
   NB: text-only (no figures); source is 2014 so all doses/intervals (esp. anticoagulation timing) must be checked against current institutional/ASRA guidance. Appendix A's normal-value tables and Appendix H acupuncture were not reproduced verbatim.


7. **Emergency Procedures (Ch15)** was already built in a prior session (2 entries: cricothyrotomy, pericardiocentesis/IO) and fully covers the chapter's actual narrow content (hands-on emergency procedures only — MH/anaphylaxis/LAST are not standalone entries in this edition).

### Appendix tables expanded (follow-up)
Per request, three appendix tables were pulled out as their own detailed reference entries (beyond the summary frameworks):
- **ref-preop-testing** (App A): ECG/CXR/Hb/renal/LFT/coag indication lists + diagnosis-based testing approach (Table A-1).
- **ref-vte-ponv-prophylaxis** (App B): VTE risk-level → prophylaxis grid (mechanical IPC/VFP/GCS vs pharmacologic LMWH/heparin) + the 4-factor adult PONV risk score.
- **ref-medication-management** (App F): continue-vs-hold guidance (continue beta-blockers/statins/antiseizure; hold/adjust oral hypoglycemics+insulin, often ACE-I/ARB, diuretics; anticoagulant timing; stop herbals ~1-2 wk ahead; SGLT2i days ahead; tamsulosin/cataract).
Reference section is now 7 entries. The adult-standard entry's VTE flag was trimmed to a pointer to avoid duplication. All 2014-sourced — verify dosing/intervals/agents against current guidance.
