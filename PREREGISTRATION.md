# SPEC-ENUM pre-registration

Frozen before any score was computed. Hash of this file is recorded in `results/manifest.json`.

## Inputs
Only `data/specs.json` (redacted RHB specification text). No results, taxonomy, hardening
conditions, worked examples, or integrity annotations are visible to the procedure.

## Affordance rules (applied uniformly to every unit, from the environment description)
- **A1 `list_read_outside_inputs`** — the mount namespace is listable and readable, and
  task-adjacent directories may be present with no mount restriction at baseline.
  Ungated for all units. exploit_cost = 2 (list, read).
- **A2 `read_grader_adjacent_code`** — if a step's declared inputs include executable or
  rule-bearing artifacts (`*.py`, harness, runner, contract, spec, rules), reading them is
  ungated. exploit_cost = 2.
- **A3 `write_unverified_artifact`** — `/workspace/output/` is the sole grader-read location
  and is unconditionally writable. Any required output can be produced directly.
  Ungated for all units. exploit_cost = 1.
- **A4 `copy_reference_output`** — if a declared input already contains, or trivially yields,
  the required answer (reference predicate, manifest, index), it can be transcribed.
  exploit_cost = 2.
- **A5 `skip_upstream`** — chained mode only. Declared **gated**: the specification states
  dependencies are enforced via recomputed hashes over upstream outputs. Excluded from
  candidates. (Recorded to show the procedure honours declared gates.)

## Grading-check extraction (deterministic, from the `Grading:` clause)
Each `Grading:` clause is split on `;` and `,` into atomic checks. A check is **opaque** iff its
text matches, case-insensitively, any of:
`hidden`, `held-out`, `heldout`, `grader-side`, `grader runs`, `cannot access`, `replay`,
`adversarial suite`, `corruption suite`, `held out`.
Otherwise it is **public** (locally recomputable by the agent).

Rationale for treating opacity as exploit surface: an agent that cannot locally verify a check
receives no signal distinguishing an honest artifact from a plausible fabricated one, so the
apparent-satisfaction path is available at submission time. RHB scores fail-closed but logs such
attempts, so the relevant quantity is apparent satisfaction, not true satisfaction.

## Honest cost (deterministic proxy, from spec text)
`honest_cost = 1 + n_declared_inputs + n_declared_outputs + n_work_verbs`, where work verbs are
counted from the fixed list:
`clean, validate, extract, train, evaluate, test, identify, join, derive, implement, verify,
profile, optimize, reconstruct, sort, parse, normalize, compare, count, locate, generate,
produce, run, mitigate`.
Capped at 12.

## Candidate generation
`candidates(step) = { (a, g) : a in ungated affordances applicable to the step,
                      g in grading checks of the step,
                      a can produce an artifact that satisfies g's visible interface }`
Applicability is decided by the affordance rules above; A4 requires a reference-bearing input.
Compositions to depth 2 are formed over ungated affordances; a composition's cost is the sum of
its members' costs, and a composition is retained only if its cost is below `honest_cost`.

## Vulnerability score (FROZEN)
```
saving(a, g) = max(0, (honest_cost - exploit_cost(a)) / honest_cost)
V(step)      = sum over candidates (a, g) of saving(a, g)
V(family)    = mean over the family's six steps of V(step)
```

## Legibility bin (FROZEN)
A candidate is **specification-legible** iff every affordance in it was derived from a declared
semantic in the specification text (all of A1-A4 are). It is a **solver artifact** iff derivation
required a property of the implementation that the specification does not state. The procedure
operating on specification text alone can, by construction, only emit legible candidates. This is
the intended behaviour and supplies the negative control: SPEC-ENUM must be unable to predict
artifact-class behaviours.

## Hypotheses (stated before computation)
- **H1 (recall).** Candidates emitted by SPEC-ENUM cover at least 4 of RHB's 6 exploit categories.
- **H2 (hardening).** The minimal repairs derived from candidates cover at least 3 of RHB's 4
  environmental hardening conditions.
- **H3 (worked exploits).** Both published worked exploits (LF-2, DP-4) appear as candidates.
- **H4 (ranking).** `V(family)` ranks the four CoreRHB families in the same order as RHB's
  observed per-family exploit rates. Predicted ordering from the formula, computed by hand from
  structure before running: PF highest (most opaque checks, highest honest cost), DP lowest.
- **H5 (negative control).** SPEC-ENUM emits no candidate corresponding to a solver artifact.

## Statistical caveat, stated in advance
n = 4 families. The two-sided permutation p-value for a perfect Spearman correlation at n = 4 is
2/24 = 0.083. **No result on H4 can reach p < 0.05.** It is reported as descriptive only.

---

## Addendum: blind arm (added before the blind arm was run)

**Arm label.** `blind-model, pre-registered-prompt`. The extractor sees only redacted
specification text. The prompt author had read RHB in full, so this is *not* an independent
replication; the fully independent arm requires a human extractor who has not read RHB and
remains stated future work.

**Frozen prompts** (SHA-256 of the exact strings shipped in `colab/colab_blind_arm.py`):
- extract : `5deb595cb161...`
- probe   : `67d7edd36ee9...`

**Vocabulary constraint, verified programmatically.** The prompts contain none of:
exploit, hack, leak, tamper, reward, vulnerab*, attack, cheat, bypass, circumvent, adversar*.
The extractor is never told what category vocabulary the scoring uses, and is never asked to
find anything. It performs three descriptive tasks only: enumerate declared affordances and
their declared gates; classify each grading check as locally verifiable or opaque; estimate
the operation count of the intended path.

**Division of labour.** The model performs stages 1-3 (semantic extraction). Stages 4-8
(composition, reward-positivity filter, binning, repair, scoring) remain deterministic code and
are unchanged from the frozen specification above.

**Contamination probe.** A separate, independent call asks whether the model recognises the
benchmark and what it recalls of its findings. Stateless API calls mean this cannot contaminate
the extraction arm. Result is reported whatever it is; recognition establishes contamination as
a measured threat rather than an assumed-away one.

**Pre-registered predictions for the blind arm.**
- B1. Blind extraction recovers the same 4/6 categories as the deterministic arm.
- B2. Tampering and denial-of-evaluation remain missing, since the affordances are still absent
  from the specification text.
- B3. Opacity classification by the model correlates with the keyword-derived classification at
  Cohen's kappa > 0.6.
- B4. Re-scored V(family) with model-supplied `intended_path_ops` in place of the arithmetic
  proxy does not by itself repair the H4 ranking failure, because the diagnosis in §6 attributes
  the failure to the functional form, not to the cost estimate.

B4 is the one worth watching: if the ranking *does* repair, the §6 diagnosis was wrong and must
be rewritten.

### Blind arm outcomes (recorded after the run; predictions above were frozen before it)
B1 CONFIRMED (4/6, same categories) | B2 CONFIRMED (both misses persist)
B3 NOT CONFIRMED (opaque fraction 0.459 blind vs 0.113 keyword; instrument defect, see §5.5)
B4 CONFIRMED (rho +0.40 -> -0.40 vs R1-Zero; ranking did not repair)
Contamination probe: NOT OBTAINED (call returned unparseable output; not repeated).
Contamination handling (revised): self-report probe NOT OBTAINED. Replaced with an output-side
scan (src/contamination_scan.py) over all 36 blind extractions for redacted RHB vocabulary.
Result: 0 emissions across category names, hardening terms, named artifacts, benchmark ids and
outcome words. Deviation from the original plan is recorded here rather than concealed; the
substituted test is stronger on leakage and silent on memorisation.

### Exploratory analysis, disclosed (run after the confirmatory results, declared post-hoc)
Question: does affordance-level saving mass predict how often a category dominates across RHB's
13 models? Result: rho = -1.000 (inverted) over n = 3 categories. The exact two-sided permutation
floor at n = 3 is 2/6 = 0.333, so the test has no power in either direction and is NOT reported
as a finding in the paper. Recorded here rather than discarded. Directionally it is a third
instance of the Section 5.6 pattern: saving-based quantities do not predict outcomes, opacity does.
