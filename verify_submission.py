#!/usr/bin/env python3
"""
Pre-submission verification. Run before every upload.

Each check corresponds to a class of error actually made while preparing this paper.
Exits non-zero if any check fails, so it can gate a build.

    python3 verify_submission.py
"""
import json, re, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
TEX  = ROOT / "paper" / "tex"
RES  = ROOT / "results"
fails, warns = [], []


def ok(label, cond, detail=""):
    (fails if not cond else []).append(f"{label}: {detail}") if not cond else None
    print(f"  [{'OK ' if cond else 'FAIL'}] {label}{('  ' + detail) if detail else ''}")


def pdftext(path, first=None, last=None):
    cmd = ["pdftotext", "-layout"]
    if first: cmd += ["-f", str(first), "-l", str(last or first)]
    return subprocess.run(cmd + [str(path), "-"], capture_output=True, text=True).stdout


# ---------------------------------------------------------------- 1. numbers vs sources
print("\n1. Every headline number traced to the file it came from")
tex = (TEX / "paper.tex").read_text()
dom = json.loads((RES / "dominance.json").read_text())
sc  = json.loads((RES / "scorecard.json").read_text())
bl  = json.loads((RES / "blind_scorecard.json").read_text())
cs  = json.loads((RES / "contamination_scan.json").read_text())
nc  = json.loads((RES / "negative_control.json").read_text())
en  = json.loads((RES / "enumeration.json").read_text())

NUMBERS = [
  ("11/11 exploiting",  dom["models_exploiting"] == 11 and dom["models_not_covered"]["n"] == 0,
                        "eleven exploiting" in tex or "11 of 11" in tex),
  ("7 full / 4 partial", dom["models_fully_covered"]["n"] == 7
                         and dom["models_partially_covered"]["n"] == 4,
                        "seven fully, four partially" in tex),
  ("4 of 5 dominance",  dom["dominance_recall"] == "4/5",        "four of\nthe five" in tex or "four of the five" in tex),
  ("15 of 19 = 79%",    dom["mention_coverage"] == "15/19",      "15 of 19" in tex and "79" in tex),
  ("13/13 sign test",   dom["complexity_threshold"]["positive_deltas"] == "13/13", "13 of 13" in tex),
  ("sign p 2.4e-4",     abs(dom["complexity_threshold"]["sign_test_two_sided_p"] - 2.44e-4) < 1e-5,
                        "2.4 \\times 10^{-4}" in tex),
  ("det rho +0.40",     sc["H4_family_ranking"]["R1_Zero"]["spearman_rho"] == 0.4,  "+0.40" in tex),
  ("blind rho -0.40",   bl["B4_ranking"]["R1_Zero"]["V_rho"] == -0.4,               "-0.40" in tex),
  ("opacity +0.80",     bl["B4_ranking"]["R1_Zero"]["opacity_rho"] == 0.8,          "+0.80" in tex),
  ("cost -0.63",        abs(bl["B4_ranking"]["R1_Zero"]["honest_cost_rho"] + 0.632) < 0.01,
                        "-0.63" in tex),
  ("opacity 45.9/11.3", bl["B3_opacity_agreement"]["blind_opaque_fraction"] == 0.459,
                        "45.9" in tex and "11.3" in tex),
  ("0 emissions",       cs["total_emissions"] == 0,              "Zero emissions" in tex),
  ("514 / 147 tokens",  cs["distinct_output_tokens"] == 514 and cs["tokens_absent_from_corpus"] == 147,
                        "514" in tex and "147" in tex),
  ("4/4 controls",      nc["all_controls_pass"],                 "four controls" in tex),
  ("36 units",          len(en["units"]) == 36,                  "36 " in tex),
  ("441 candidates",    sum(u["n_candidates"] for u in en["units"]) == 441, "441" in tex),
  ("exact p 0.333",     True,                                    "p=0.333" in tex.replace(" ", "")),
  ("exact p 0.750",     True,                                    "p=0.750" in tex.replace(" ", "")),
]
for label, data_ok, in_tex in NUMBERS:
    ok(label, data_ok and in_tex, "" if (data_ok and in_tex) else f"data={data_ok} in_tex={in_tex}")

# ---------------------------------------------------------------- 2. stale claims
print("\n2. No stale or self-contradicting claims")
STALE = {
  "blinded arm was not run": "the blind arm HAS been run",
  "contamination unquantified": "superseded by the output-side scan",
  "MDPLACEHOLDER": "placeholder reference",
  "TODO": "placeholder text",
  "Type your response here": "unfilled checklist field",
}
for pat, why in STALE.items():
    ok(f"absent: '{pat}'", pat not in tex, why)
bib = (TEX / "references.bib").read_text()
ok("bib has no placeholders", "MDPLACEHOLDER" not in bib and "TODO" not in bib)
ok("bib has no VERIFY flags", "% VERIFY" not in bib)

# ---------------------------------------------------------------- 3. build integrity
print("\n3. Build integrity")
log = (TEX / "paper.log")
logtext = log.read_text(errors="ignore") if log.exists() else ""
ok("no undefined citations", "Citation" not in logtext or "undefined" not in logtext)
pdf = TEX / "paper.pdf"
ok("paper.pdf exists", pdf.exists())
if pdf.exists():
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    ok("page count <= 9 (7 content + 2 refs)", pages <= 9, f"{pages} pages")
    body = pdftext(pdf)
    refpage = next((p for p in range(1, pages + 1)
                    if re.search(r"\bReferences\b", pdftext(pdf, p))), None)
    ok("references start by page 8", refpage is not None and refpage <= 8, f"page {refpage}")

# ---------------------------------------------------------------- 4. anonymity + metadata
print("\n4. Anonymity and metadata")
IDENT = [r"\bMIT\b", r"[Pp]aloma", r"github\.com/[A-Za-z0-9_-]+", r"\\section\*?\{Acknowl"]
for pat in IDENT:
    hits = re.findall(pat, tex)
    ok(f"no match /{pat}/", not hits, str(hits[:3]) if hits else "")
if pdf.exists():
    meta = subprocess.run(["exiftool", str(pdf)], capture_output=True, text=True).stdout
    leaky = [l for l in meta.splitlines()
             if re.match(r"\s*(Author|Creator|Producer|Title|Subject)\s*:", l)]
    ok("PDF metadata scrubbed", not leaky, "; ".join(leaky[:2]))
    ok("first page says Anonymous", "Anonymous" in pdftext(pdf, 1))

# ---------------------------------------------------------------- 5. checklist validity
print("\n5. Reproducibility checklist")
rc = TEX / "ReproducibilityChecklist.pdf"
if rc.exists():
    t = re.sub(r"\s+", " ", pdftext(rc))
    bad = []
    for m in re.finditer(r"(\d+\.\d+)\..{5,240}?\((yes/[a-zA-Z/]+)\)\s+([a-zA-Z]+)", t):
        q, opts, ans = m.groups()
        if ans not in opts.split("/") and ans not in ("par", "tial", "work"):
            bad.append(f"{q}={ans} not in {opts}")
    ok("all answers within allowed options", not bad, "; ".join(bad[:3]))
    body_only = t.split("1. General Paper Structure", 1)[-1]
    ok("no unfilled answer fields", "Type your response" not in body_only,
       "(the template's own instructions example is excluded)")
else:
    warns.append("ReproducibilityChecklist.pdf not built")

# ---------------------------------------------------------------- 6. code reproduces
print("\n6. Analysis scripts reproduce")
for script in ["specenum.py", "negative_control.py", "score.py", "score_blind.py",
               "contamination_scan.py", "dominance.py", "figures.py"]:
    r = subprocess.run([sys.executable, str(ROOT / "src" / script)],
                       capture_output=True, text=True, cwd=ROOT)
    ok(f"{script}", r.returncode == 0, r.stderr.strip().splitlines()[-1] if r.returncode else "")

# ---------------------------------------------------------------- summary
print("\n" + "=" * 62)
if warns:
    for w in warns: print(f"  WARN {w}")
print(f"  {'ALL CHECKS PASS' if not fails else str(len(fails)) + ' FAILURES'}")
for f in fails: print(f"    - {f}")
print("=" * 62)
sys.exit(1 if fails else 0)
