# SPEC-ENUM — forward enumeration of specification-licensed behavior

Reproduces every number in the paper. Deterministic; no API key, no network, no seeds.

    python3 src/specenum.py         # stages 1-8 over the redacted corpus -> results/enumeration.json
    python3 src/negative_control.py # hide-and-seek control            -> results/negative_control.json
    python3 src/score.py            # H1-H5 vs RHB ground truth         -> results/scorecard.json

## Layout
    src/PREREGISTRATION.md   frozen rules, formula, hypotheses, statistical caveat
    src/specenum.py          the procedure
    src/negative_control.py  falsifiability control on Baker et al. primitives
    src/score.py             scoring against RHB published ground truth
    src/score_blind.py       scoring of the blind arm, predictions B1-B4
    src/contamination_scan.py output-side leakage scan over the blind extractions
    data/specs.json          redacted RHB corpus + full redaction protocol
    results/                 enumeration, control, scorecard, file manifest
    paper/paper.md           the paper
    paper/reproducibility_checklist_updated.md

## Headline
    H1 category recall      CONFIRMED    4/6, both misses traceable to undeclared affordances
    H2 hardening coverage   UNTESTED     repair vocabulary was contaminated; needs blind arm
    H3 worked exploits      CONFIRMED    2/2 at affordance-type level, 0/2 at artifact level
    H4 family ranking       NOT CONFIRMED  rho=+0.40 (R1-Zero), 0.00 (V3), n=4
    H5 negative control     CONFIRMED    4/4; vertical launch provably not derivable

Requires: python3, numpy, scipy.

## Blind arm outcomes
    B1 categories        CONFIRMED     4/6, same as deterministic arm
    B2 misses persist    CONFIRMED     tampering + denial-of-evaluation still absent
    B3 opacity agrees    NOT CONFIRMED 0.459 blind vs 0.113 keyword -> instrument defect
    B4 ranking repairs?  CONFIRMED NO  rho +0.40 -> -0.40; diagnosis stands
    contamination        0 emissions of redacted vocabulary in 36 extractions

    Key single finding: opacity alone rho=+0.80 vs observed rates, honest cost rho=-0.63.
    Two arms with different extractors converge on the same attribution. Not refitted.
