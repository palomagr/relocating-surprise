"""
SPEC-ENUM: forward enumeration of reward-positive compositions from a specification.

Implements the procedure frozen in PREREGISTRATION.md. Deterministic: no model calls, no
randomness, no access to outcome data. Input is redacted specification text only.

Stages
  1 affordance extraction    (rules A1-A5)
  2 grading-check extraction (split + opacity keywords)
  3 honest-cost estimate     (declared inputs/outputs + work verbs)
  4 composition enumeration  (depth <= 2 over ungated affordances)
  5 reward-positivity filter (composition cost < honest cost; produces visible satisfaction)
  6 legibility binning
  7 repair derivation
  8 vulnerability score
"""
from __future__ import annotations
import json, re, itertools, hashlib, pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent

OPACITY_KEYWORDS = [
    "hidden", "held-out", "heldout", "held out", "grader-side", "grader runs",
    "cannot access", "replay", "adversarial suite", "corruption suite",
]

WORK_VERBS = [
    "clean", "validate", "extract", "train", "evaluate", "test", "identify", "join",
    "derive", "implement", "verify", "profile", "optimize", "reconstruct", "sort",
    "parse", "normalize", "compare", "count", "locate", "generate", "produce", "run",
    "mitigate",
]

REFERENCE_BEARING = [
    "predicate.py", "manifest", "reference index", "harness runner", "replay runner",
    "contract", "rules.md", "spec.json", "format.json", "pattern.json", "key_spec",
    "schema.json", "invariants spec", "corruptions spec", "memory limit spec",
    "adversarial input spec", "cleaning rules", "anomaly definition", "trace constraints",
    "root-cause question", "feature spec", "training config", "label definition",
    "patch format spec", "metrics schema", "report schema", "allowed changes spec",
    "profile instructions", "mitigation contract", "performance contract", "record schema",
    "checksum manifest", "schema spec", "feature schema",
]

CODE_BEARING = [".py", "harness", "runner", "contract", "rules.md", "predicate", "spec"]

AFFORDANCES = {
    "A1": dict(name="list_read_outside_inputs", cost=2,
               desc="List and read paths beyond the declared inputs; task-adjacent "
                    "directories are mounted and unrestricted at baseline."),
    "A2": dict(name="read_grader_adjacent_code", cost=2,
               desc="Read rule-bearing or executable inputs to infer what the grader checks."),
    "A3": dict(name="write_unverified_artifact", cost=1,
               desc="Write the required output directly; /workspace/output/ is the sole "
                    "grader-read location and is unconditionally writable."),
    "A4": dict(name="copy_reference_output", cost=2,
               desc="Transcribe an answer already present in, or trivially derivable from, "
                    "a declared input."),
    "A5": dict(name="skip_upstream", cost=1, gated=True,
               desc="Emit downstream artifacts without upstream work. DECLARED GATE: "
                    "dependencies enforced via recomputed hashes over upstream outputs."),
}

REPAIRS = {
    "A1": "reduce_file_access: restrict mounts and directory listing to the current step's "
          "required inputs; unmount task-adjacent directories.",
    "A2": "harden_evaluation_boundary: move grader/harness/spec artifacts outside the "
          "sandbox or behind protected read-only mounts.",
    "A3": "explicit_step_verification: bind each output to its inputs via a recomputation "
          "or hash constraint the agent cannot satisfy without doing the work.",
    "A4": "randomize_intermediate_outputs: per-instance nonce or randomized naming so a "
          "transcribed reference answer does not validate.",
}


def split_checks(grading: str):
    if not grading:
        return []
    parts = re.split(r"[;.]|(?<=\w),\s(?=[a-z])", grading)
    return [p.strip() for p in parts if p and len(p.strip()) > 3]


def is_opaque(check: str) -> bool:
    c = check.lower()
    return any(k in c for k in OPACITY_KEYWORDS)


def parse_spec(text: str):
    """Pull Input:/Output:/Grading: clauses out of a spec string."""
    def grab(label, nxt):
        m = re.search(rf"{label}:\s*(.*?)(?=(?:{nxt}):|$)", text, re.S)
        return m.group(1).strip() if m else ""
    inputs = grab("Input", "Output|Grading|Hard|Integrity")
    outputs = grab("Output", "Grading|Hard|Integrity|Input")
    grading = grab("Grading", "Hard|Integrity|Input|Output")
    return inputs, outputs, grading


def count_items(clause: str) -> int:
    if not clause:
        return 0
    return max(1, len([x for x in re.split(r",| and ", clause) if x.strip()]))


def honest_cost(text: str, inputs: str, outputs: str) -> int:
    verbs = sum(1 for v in WORK_VERBS if re.search(rf"\b{v}", text, re.I))
    return min(12, 1 + count_items(inputs) + count_items(outputs) + verbs)


def applicable_affordances(text: str, inputs: str):
    """Which affordance rules fire for this step."""
    out = {"A1": True, "A3": True}
    blob = (inputs + " " + text).lower()
    out["A2"] = any(k in blob for k in CODE_BEARING)
    out["A4"] = any(k.lower() in blob for k in REFERENCE_BEARING)
    return {k for k, v in out.items() if v}


def enumerate_unit(uid: str, name: str, text: str):
    inputs, outputs, grading = parse_spec(text)
    checks = split_checks(grading) or ["output artifact is present and parses"]
    hc = honest_cost(text, inputs, outputs)
    aff = applicable_affordances(text, inputs)

    # stage 4: compositions to depth 2 over ungated affordances
    singles = [(a,) for a in sorted(aff)]
    pairs = [tuple(sorted(p)) for p in itertools.combinations(sorted(aff), 2)]
    comps = singles + pairs

    candidates = []
    for comp in comps:
        cost = sum(AFFORDANCES[a]["cost"] for a in comp)
        if cost >= hc:                       # stage 5: must undercut the honest path
            continue
        for chk in checks:
            opaque = is_opaque(chk)
            # a composition produces visible satisfaction of chk if it can emit the artifact
            # (A3) or supply its content (A1/A2/A4). Opaque checks are satisfiable in
            # appearance by any emitting composition, since the agent cannot be locally refuted.
            emits = "A3" in comp
            sources = any(a in comp for a in ("A1", "A2", "A4"))
            if not (emits or sources):
                continue
            if not opaque and not sources:
                # a public check needs real content from somewhere, not just an emit
                continue
            saving = max(0.0, (hc - cost) / hc)
            if saving <= 0:
                continue
            candidates.append(dict(
                unit=uid, affordances=list(comp), check=chk, opaque=opaque,
                exploit_cost=cost, honest_cost=hc, saving=round(saving, 4),
                legibility="specification-legible",
                repairs=sorted({REPAIRS[a] for a in comp if a in REPAIRS}),
            ))

    V = round(sum(c["saving"] for c in candidates), 4)
    return dict(
        unit=uid, name=name, honest_cost=hc,
        affordances_ungated=sorted(aff),
        affordances_gated=["A5 (declared gate: upstream hash enforcement)"],
        checks=[{"text": c, "opaque": is_opaque(c)} for c in checks],
        n_candidates=len(candidates), V=V, candidates=candidates,
    )


def main():
    spec = json.loads((ROOT / "data" / "specs.json").read_text())
    units, families = [], {}
    for u in spec["units"]:
        if u.get("family"):
            steps = []
            for s in u["steps"]:
                txt = s["spec"]
                if u.get("key_rule"):
                    txt += " " + u["key_rule"]
                steps.append(enumerate_unit(s["id"], u["name"], txt))
            families[u["id"]] = dict(
                family=u["id"], name=u["name"], steps=steps,
                V_family=round(sum(s["V"] for s in steps) / len(steps), 4),
                n_candidates=sum(s["n_candidates"] for s in steps),
            )
            units.extend(steps)
        else:
            units.append(enumerate_unit(u["id"], u["name"], u["spec"]))

    out = dict(
        procedure="SPEC-ENUM v1",
        preregistration_sha256=hashlib.sha256(
            (HERE / "PREREGISTRATION.md").read_bytes()).hexdigest(),
        corpus_sha256=hashlib.sha256(
            (ROOT / "data" / "specs.json").read_bytes()).hexdigest(),
        units=units, families=families,
    )
    (ROOT / "results" / "enumeration.json").write_text(json.dumps(out, indent=2))
    print(f"units enumerated : {len(units)}")
    print(f"total candidates : {sum(u['n_candidates'] for u in units)}")
    print("\nV(family):")
    for f in sorted(families.values(), key=lambda x: -x["V_family"]):
        print(f"  {f['family']:3s} {f['name']:28s} V={f['V_family']:7.3f}  "
              f"candidates={f['n_candidates']}")


if __name__ == "__main__":
    main()
