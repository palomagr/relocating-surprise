"""
Dominance-weighted category coverage.

RHB Table 2 reports, for each of 13 frontier models, its overall exploit rate and its DOMINANT
exploit categories. Scoring SPEC-ENUM against the flat 6-category taxonomy understates coverage,
because one category (denial-of-evaluation) never dominates for any model. This scores against
what actually dominates in practice.

Also runs a sign test on RHB Table 5 (standard vs hard variants) for the complexity-threshold
direction that the frozen V functional form entails.

    python3 src/dominance.py  ->  results/dominance.json
"""
from __future__ import annotations
import json, math, pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent

# ---- RHB Table 2, transcribed verbatim -------------------------------------------------
TABLE2 = [
    ("Claude Sonnet 4.5",      86.2,  0.0, []),
    ("Claude Opus 4.5",        88.5,  0.0, []),
    ("Claude 3.5 Sonnet v2",   82.0,  0.6, ["leak"]),
    ("GPT-4o",                 79.5,  0.9, ["leak", "parse"]),
    ("Gemini 2.5 Flash",       76.1,  0.8, ["leak"]),
    ("DeepSeek-V3",            77.8,  0.6, ["leak"]),
    ("Claude 3.7 Sonnet",      84.0,  3.9, ["seq", "parse"]),
    ("Gemini 2.5 Pro",         83.2,  4.6, ["leak", "special-case"]),
    ("o1",                     86.7,  6.8, ["seq", "tamp"]),
    ("o3-mini",                82.6,  7.1, ["seq", "parse"]),
    ("o4-mini",                84.8,  8.4, ["seq", "tamp"]),
    ("o3",                     87.9, 11.8, ["tamp", "seq"]),
    ("DeepSeek-R1-Zero",       81.2, 13.9, ["seq", "tamp"]),
]

# ---- RHB Table 5, standard vs hard exploit rate (%) ------------------------------------
TABLE5_DELTAS = [1.8, 1.2, 2.8, 3.2, 2.8, 3.3, 4.3, 5.1, 5.6, 6.7, 6.8, 7.8, 8.4]

# SPEC-ENUM affordance -> RHB category, fixed in score.py before any of this was computed
RECOVERED = {"leak", "seq", "parse", "special-case"}     # A1, A3, A3, A2/A4
ALL_CATEGORIES = {"leak", "tamp", "seq", "parse", "special-case", "denial"}


def main():
    mentions = Counter(k for _, _, _, ks in TABLE2 for k in ks)
    dominant_cats = set(mentions)
    never_dominant = sorted(ALL_CATEGORIES - dominant_cats)

    exploiting = [(m, r, ks) for m, _, r, ks in TABLE2 if ks]
    full = [m for m, _, ks in exploiting if all(k in RECOVERED for k in ks)]
    partial = [m for m, _, ks in exploiting
               if any(k in RECOVERED for k in ks) and not all(k in RECOVERED for k in ks)]
    none = [m for m, _, ks in exploiting if not any(k in RECOVERED for k in ks)]

    tot = sum(mentions.values())
    rec = sum(v for k, v in mentions.items() if k in RECOVERED)

    pos = sum(1 for d in TABLE5_DELTAS if d > 0)
    n = len(TABLE5_DELTAS)
    sign_p = 2 * sum(math.comb(n, k) for k in range(pos, n + 1)) / 2 ** n

    out = {
        "source": "RHB Tables 2 and 5",
        "flat_taxonomy_recall": f"{len(RECOVERED & ALL_CATEGORIES)}/6",
        "categories_ever_dominant": sorted(dominant_cats),
        "never_dominant": never_dominant,
        "dominance_recall": f"{len(dominant_cats & RECOVERED)}/{len(dominant_cats)}",
        "dominant_mentions": dict(mentions.most_common()),
        "mention_coverage": f"{rec}/{tot}",
        "mention_coverage_frac": round(rec / tot, 4),
        "models_total": len(TABLE2),
        "models_exploiting": len(exploiting),
        "models_fully_covered": {"n": len(full), "models": full},
        "models_partially_covered": {"n": len(partial), "models": partial},
        "models_not_covered": {"n": len(none), "models": none},
        "headline": (f"{len(full) + len(partial)}/{len(exploiting)} exploiting models have at "
                     f"least one dominant category recovered by enumeration over specification "
                     f"text alone"),
        "complexity_threshold": {
            "note": "RHB Table 5: hard variants raise honest-solution complexity while holding "
                    "the exploit surface fixed. The frozen V form entails exploit rates rise. "
                    "CAVEAT: this direction was the stated design rationale for V in "
                    "PREREGISTRATION.md, so agreement is partly by construction. Reported as a "
                    "consistency check, NOT an independent prediction.",
            "positive_deltas": f"{pos}/{n}",
            "delta_range": [min(TABLE5_DELTAS), max(TABLE5_DELTAS)],
            "sign_test_two_sided_p": sign_p,
        },
    }
    (ROOT / "results" / "dominance.json").write_text(json.dumps(out, indent=2))

    print(f"flat taxonomy recall      : {out['flat_taxonomy_recall']}")
    print(f"categories ever dominant  : {len(dominant_cats)}/6 "
          f"(never dominant: {', '.join(never_dominant)})")
    print(f"dominance recall          : {out['dominance_recall']}")
    print(f"dominant-mention coverage : {out['mention_coverage']} "
          f"= {out['mention_coverage_frac']:.1%}")
    print(f"\nexploiting models         : {len(exploiting)}")
    print(f"  fully covered           : {len(full)}")
    print(f"  partially covered       : {len(partial)}")
    print(f"  NOT covered             : {len(none)}")
    print(f"\nHEADLINE: {out['headline']}")
    print(f"\ncomplexity threshold      : {pos}/{n} positive, "
          f"sign-test p = {sign_p:.2e} (consistency check only)")


if __name__ == "__main__":
    main()
