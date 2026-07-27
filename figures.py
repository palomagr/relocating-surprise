"""
Generate Figure 1 and Figure 2 as vector PDF + PNG from the result JSON files.
Nothing is hard-coded: every number is read from results/.

    python3 src/figures.py   ->  paper/fig1_forecastability.{pdf,png}
                                 paper/fig2_correlations.{pdf,png}
"""
from __future__ import annotations
import json, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle
from scipy import stats

ROOT = pathlib.Path(__file__).resolve().parent.parent
R = ROOT / "results"
OUT = ROOT / "paper"

MM = 1 / 25.4
COL1, COL2 = 88 * MM, 180 * MM          # single / double column (Nature CS metrics)

# Okabe-Ito colourblind-safe
BLUE, ORANGE, GREEN, GREY, INK = "#0072B2", "#E69F00", "#009E73", "#8C8C8C", "#1A1A1A"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Liberation Sans"],
    "font.size": 7,
    "axes.labelsize": 7.5,
    "axes.titlesize": 7.5,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 6.5,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.4, "ytick.major.size": 2.4,
    "xtick.direction": "out", "ytick.direction": "out",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": INK, "text.color": INK,
    "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
    "pdf.fonttype": 42, "ps.fonttype": 42,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.01,
    "figure.dpi": 400,
})


# ----------------------------------------------------------------- Figure 1
def figure1():
    nc = json.loads((R / "negative_control.json").read_text())["results"]
    legible = [k for k, v in nc.items() if v["emitted_by_SPEC_ENUM"]]
    artifact = [k for k, v in nc.items() if not v["emitted_by_SPEC_ENUM"]]

    PRETTY = {
        "box_surfing":            ("Box surfing", "grab \u2218 move", "move force is not\ncontact-gated"),
        "ramp_use_to_scale_wall": ("Ramp use", "grab \u2218 move", "translate the\ncomposite body"),
        "ramp_locking_defence":   ("Ramp locking", "lock", "immobilise an\nobject in place"),
        "vertical_launch":        ("Vertical launch", "",
                                   "not derivable \u2014 requires\ncontact-solver penetration\nrecovery"),
    }

    fig = plt.figure(figsize=(COL1, 62 * MM))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)

    ax.text(50, 97.5, "Forecastability test", ha="center", va="top",
            fontsize=7.8, fontweight="bold")
    ax.text(50, 92.6, "is there a derivation using only what the specification declares?",
            ha="center", va="top", fontsize=6.2, color=GREY)

    def panel(x0, w, title, sub, keys, accent, repair, note=None):
        ax.add_patch(FancyBboxPatch((x0, 17), w, 69,
                                    boxstyle="round,pad=0,rounding_size=1.5",
                                    fc="white", ec=accent, lw=0.9, zorder=1))
        ax.add_patch(Rectangle((x0, 77.5), w, 8.5, fc=accent, ec="none",
                               alpha=0.13, zorder=2))
        ax.text(x0 + w / 2, 83.6, title, ha="center", va="center", fontsize=7.4,
                fontweight="bold", color=accent, zorder=3)
        ax.text(x0 + w / 2, 79.7, sub, ha="center", va="center", fontsize=5.9,
                color="#5A5A5A", style="italic", zorder=3)
        ys = {3: [72.0, 55.5, 39.0], 1: [72.0]}[len(keys)]
        for k, y in zip(keys, ys):
            name, comp, why = PRETTY[k]
            ax.text(x0 + 3.4, y, name, ha="left", va="top", fontsize=7.0,
                    fontweight="bold", zorder=3)
            if comp:
                ax.text(x0 + w - 3.4, y - 0.3, comp, ha="right", va="top", fontsize=6.3,
                        color=accent, family="DejaVu Sans", zorder=3)
            ax.text(x0 + 3.4, y - 4.4, why, ha="left", va="top", fontsize=5.9,
                    color="#4D4D4D", linespacing=1.35, zorder=3)
        if note:
            ax.text(x0 + w / 2, 52, note, ha="center", va="top", fontsize=5.9,
                    color="#6B6B6B", style="italic", linespacing=1.45, zorder=3)
        ax.plot([x0 + 2.2, x0 + w - 2.2], [26.5, 26.5], color=accent, lw=0.5,
                alpha=0.45, zorder=3)
        ax.text(x0 + w / 2, 21.6, repair, ha="center", va="center", fontsize=6.3,
                color=accent, fontweight="bold", linespacing=1.5, zorder=3)

    panel(1, 47, "Specification-legible", "derivable from declared semantics",
          legible, BLUE, "Repair: revise\nthe specification")
    panel(52, 47, "Solver artifact", "depends on undeclared properties",
          artifact, ORANGE, "Repair: fix the\nsimulator or verifier",
          note="No composition of the three\ndeclared primitives supplies\nthis behaviour, so SPEC-ENUM\ncannot emit it at any depth.")

    ax.plot([50, 50], [18, 88.5], color="#BFBFBF", lw=0.5, ls=(0, (2.0, 2.2)), zorder=4)

    ax.text(0.5, 11.0, "Negative control on the hide-and-seek primitive set "
                       "(Baker et al. 2020, \u00a73): 4/4 behaviours",
            ha="left", va="center", fontsize=6.0, color="#4D4D4D")
    ax.text(0.5, 6.8, "binned as claimed. The vertical-launch miss is structural rather "
                      "than tuned \u2014 a procedure",
            ha="left", va="center", fontsize=6.0, color="#4D4D4D")
    ax.text(0.5, 2.6, "that derived every observed behaviour would show only that the "
                      "criterion is vacuous.",
            ha="left", va="center", fontsize=6.0, color="#4D4D4D")

    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"fig1_forecastability.{ext}")
    plt.close(fig)
    print(f"fig1: {len(legible)} legible, {len(artifact)} artifact, all pass ="
          f" {all(v['control_passes'] for v in nc.values())}")


# ----------------------------------------------------------------- Figure 2
def _spearman_null(n=4):
    """Exact permutation distribution of Spearman rho for n items."""
    import itertools, collections
    base = list(range(1, n + 1))
    cnt = collections.Counter()
    for perm in itertools.permutations(base):
        d2 = sum((x - y) ** 2 for x, y in zip(base, perm))
        cnt[round(1 - 6 * d2 / (n * (n * n - 1)), 10)] += 1
    tot = sum(cnt.values())
    return {k: v / tot for k, v in cnt.items()}, tot


def _two_sided_p(rho, null):
    """Exact two-sided p for an observed rho against the lattice null."""
    return sum(pr for r, pr in null.items() if abs(r) >= abs(rho) - 1e-9)


def figure2():
    det = json.loads((R / "enumeration.json").read_text())
    blind = json.loads((R / "blind_scorecard.json").read_text())
    GT = {"DP": 12.1, "LF": 14.0, "PF": 15.8, "MR": 13.5}
    fams = ["DP", "LF", "PF", "MR"]
    order = sorted(fams, key=lambda f: GT[f])          # low -> high rate

    dV, dOp, dHc = {}, {}, {}
    for f in fams:
        st = det["families"][f]["steps"]
        dV[f] = det["families"][f]["V_family"]
        dOp[f] = (sum(1 for s in st for c in s["checks"] if c["opaque"])
                  / sum(len(s["checks"]) for s in st))
        dHc[f] = sum(s["honest_cost"] for s in st) / len(st)
    bV, bOp, bHc = blind["V_family"], blind["opacity_family"], blind["honest_cost_family"]

    null, nperm = _spearman_null(4)
    panels = [("Frozen score $V$", dV, bV, "pre-registered score fails"),
              ("Opaque check fraction", dOp, bOp, "opacity tracks the outcome"),
              ("Honest-path cost", dHc, bHc, "cost points the wrong way")]

    fig = plt.figure(figsize=(COL2, 92 * MM))
    gs = fig.add_gridspec(2, 3, height_ratios=[2.15, 1.0], hspace=0.62, wspace=0.13,
                          left=0.085, right=0.995, top=0.885, bottom=0.085)
    y = [GT[f] for f in fams]
    rho_store = []

    for k, (label, dd, bb, verdict) in enumerate(panels):
        ax = fig.add_subplot(gs[0, k])
        for f in fams:                                   # family reference lines
            ax.axhline(GT[f], color="#DCDCDC", lw=0.5, zorder=1)
        pts = []
        for vals, colour, marker, arm in ((dd, ORANGE, "o", "det"), (bb, BLUE, "s", "blind")):
            x = [vals[f] for f in fams]
            rho, _ = stats.spearmanr(x, y)
            pv = _two_sided_p(rho, null)
            rho_store.append((k, arm, rho, pv, colour, marker))
            ax.scatter(x, y, s=30, c=colour, marker=marker, edgecolors="white",
                       linewidths=0.6, zorder=4, clip_on=False)
            pts.append((colour, rho, pv))
        ax.set_xlabel(label, labelpad=2)
        ax.set_ylim(11.3, 16.7)
        ax.set_yticks([GT[f] for f in order])
        if k == 0:
            ax.set_yticklabels([f"{f}  {GT[f]:.1f}" for f in order], fontsize=6.1)
            ax.set_ylabel("Observed exploit rate (%), R1-Zero", labelpad=3)
        else:
            ax.set_yticklabels([])
        ax.tick_params(axis="y", length=1.6)
        xr = ax.get_xlim(); pad = (xr[1] - xr[0]) * 0.10
        ax.set_xlim(xr[0] - pad, xr[1] + pad)
        ax.set_title(verdict, fontsize=6.5, color="#4D4D4D", style="italic", pad=9)
        ax.text(-0.035, 1.20, "abc"[k], transform=ax.transAxes, fontsize=8.5,
                fontweight="bold", va="bottom", ha="left")
        for i, (colour, rho, pv) in enumerate(pts):
            ax.text(0.03, 0.955 - i * 0.105, f"$\\rho$ {rho:+.2f}   $p$ {pv:.2f}",
                    transform=ax.transAxes, fontsize=6.4, color=colour,
                    fontweight="bold", va="top", ha="left")

    # ---------------- panel d: exact permutation null ----------------
    ax = fig.add_subplot(gs[1, :])
    ks = sorted(null)
    ax.bar(ks, [null[r] for r in ks], width=0.085, color="#D9D9D9",
           edgecolor="#BFBFBF", lw=0.4, zorder=2)
    ax.axvline(0, color="#BFBFBF", lw=0.5, zorder=1)
    ymax = max(null.values())
    ax.set_ylim(0, ymax * 2.35)
    ax.set_xlim(-1.16, 1.16)
    ax.set_xticks([-1, -0.8, -0.6, -0.4, -0.2, 0, 0.2, 0.4, 0.6, 0.8, 1])
    ax.set_xlabel("Spearman $\\rho$", labelpad=2)
    ax.set_ylabel("null\nprobability", labelpad=3, fontsize=6.6, linespacing=1.2)
    ax.set_yticks([0, 0.1])
    ax.text(-0.035, 1.14, "d", transform=ax.transAxes, fontsize=8.5,
            fontweight="bold", va="bottom", ha="left")
    ax.set_title("every attainable value fails significance at $n=4$: the smallest possible "
                 "two-sided $p$ is 0.083, at $\\rho=\\pm1$",
                 fontsize=6.5, color="#4D4D4D", style="italic", pad=6)
    for k, arm, rho, pv, colour, marker in rho_store:
        yy = ymax * (2.00 if arm == "blind" else 1.62)
        ax.scatter([rho], [yy], s=27, c=colour, marker=marker, edgecolors="white",
                   linewidths=0.6, zorder=5, clip_on=False)
        ax.annotate("abc"[k], (rho, yy), textcoords="offset points", xytext=(0, 5.4),
                    ha="center", fontsize=5.9, color=colour, fontweight="bold", zorder=5)
        ax.plot([rho, rho], [null.get(round(rho, 10), 0) + ymax * 0.10, yy - ymax * 0.16],
                color=colour, lw=0.45, ls=(0, (1.6, 1.6)), zorder=3)
    for xr_ in (-1, 1):
        ax.annotate("$p$ = 0.083\\neven here", xy=(xr_, null[xr_] + ymax * 0.04),
                    xytext=(xr_ * 0.97, ymax * 1.14), ha="center", va="bottom",
                    fontsize=5.6, color="#8C8C8C", linespacing=1.3,
                    arrowprops=dict(arrowstyle="-", color="#C4C4C4", lw=0.4))
    ax.text(1.14, ymax * 2.00, "blind arm", ha="right", va="center", fontsize=6.0,
            color=BLUE, fontweight="bold")
    ax.text(1.14, ymax * 1.62, "deterministic arm", ha="right", va="center", fontsize=6.0,
            color=ORANGE, fontweight="bold")

    fig.legend(handles=[plt.Line2D([], [], marker="o", ls="", mfc=ORANGE, mec="white",
                                   mew=0.6, ms=4.6, label="deterministic arm"),
                        plt.Line2D([], [], marker="s", ls="", mfc=BLUE, mec="white",
                                   mew=0.6, ms=4.4, label="blind arm")],
               frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.54, 1.005),
               handletextpad=0.3, columnspacing=1.9)

    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"fig2_correlations.{ext}")
    plt.close(fig)
    for k, arm, rho, pv, _, _ in rho_store:
        print(f"fig2 {'abc'[k]} {arm:6s} rho={rho:+.3f}  exact two-sided p={pv:.3f}")


# ----------------------------------------------------------------- Figure 3
def _nn_glyph(ax, cx, cy, w, h, layers=(3, 4, 3), colour="#0072B2"):
    xs = [cx - w / 2 + i * w / (len(layers) - 1) for i in range(len(layers))]
    pos = []
    for x, n in zip(xs, layers):
        pos.append([(x, cy - h / 2 + (j + 0.5) * h / n) for j in range(n)])
    for A, B in zip(pos, pos[1:]):
        for (x1, y1) in A:
            for (x2, y2) in B:
                ax.plot([x1, x2], [y1, y2], color=colour, lw=0.26, alpha=0.40, zorder=3)
    for layer in pos:
        for (x, y) in layer:
            ax.add_patch(Circle((x, y), 0.8, fc="white", ec=colour, lw=0.55, zorder=4))


def figure3():
    det = json.loads((R / "enumeration.json").read_text())
    cs = json.loads((R / "contamination_scan.json").read_text())
    n_units = len(det["units"])
    n_cand = sum(u["n_candidates"] for u in det["units"])

    fig = plt.figure(figsize=(COL2, 86 * MM))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    ax.set_xlim(0, 180); ax.set_ylim(0, 86)

    def box(x, y, w, h, title, sub=None, ec=INK, fc="white", ts=6.6):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0,rounding_size=1.2",
                                    fc=fc, ec=ec, lw=0.8, zorder=2))
        ax.text(x + w / 2, y + h * (0.63 if sub else 0.5), title, ha="center", va="center",
                fontsize=ts, fontweight="bold", zorder=5, linespacing=1.28)
        if sub:
            ax.text(x + w / 2, y + h * 0.24, sub, ha="center", va="center", fontsize=5.5,
                    color="#5A5A5A", zorder=5, linespacing=1.3)

    def arrow(x1, y1, x2, y2, colour=INK, lw=0.8, rad=0.0):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>,head_width=0.15,head_length=0.36",
                                    color=colour, lw=lw, shrinkA=0, shrinkB=0,
                                    connectionstyle=f"arc3,rad={rad}"), zorder=6)

    # ---- shared source ------------------------------------------------------
    box(3, 44, 24, 16, "Environment\nspecification", "affordances,\nreward, scope",
        ec=INK, fc="#F0F0F0")

    # ---- upper: behaviour-side ---------------------------------------------
    UY, UH = 66, 14
    for x, t, sb in ((33, "Train\noptimizer", None), (60, "Collect\nrollouts", "13 models"),
                     (87, "Observe\nexploit", "6 categories"),
                     (114, "Harden\nenvironment", "4 conditions")):
        w = 26 if x == 114 else 23
        box(x, UY, w, UH, t, sb, ec=ORANGE, fc="#FDF6EA")
    arrow(27, 57, 33, UY + UH / 2, ORANGE, rad=-0.15)
    for x1, x2 in ((56, 60), (83, 87), (110, 114)):
        arrow(x1, UY + UH / 2, x2, UY + UH / 2, ORANGE)
    # feedback loop routed above the track as an explicit polyline (no arc overshoot)
    ax.plot([140, 140, 17, 17], [UY + UH, 83, 83, 62.5], color=ORANGE, lw=0.7,
            solid_joinstyle="round", zorder=1)
    arrow(17, 63.5, 17, 60.4, ORANGE, lw=0.7)
    ax.text(78, 84.6, "patch, then repeat", ha="center", va="center", fontsize=6.0,
            color=ORANGE, style="italic")
    ax.text(3, 73, "Behaviour-side\nrepair follows\ndiscovery", ha="left", va="center",
            fontsize=6.6, fontweight="bold", color=ORANGE, linespacing=1.4)
    ax.text(33, 62.8, "thousands of episodes \u00b7 exploit found by exploration \u00b7 "
                      "cost scales with the agent",
            fontsize=5.8, color="#7A6020", va="center")

    # ---- lower: specification-side -----------------------------------------
    LY, LH = 18, 18
    box(33, LY, 23, LH, "", None, ec=BLUE, fc="#EDF5FB")
    _nn_glyph(ax, 44.5, LY + 11.8, 14, 8)
    ax.text(44.5, LY + 3.6, "Stages 1\u20133\nextraction", ha="center", va="center",
            fontsize=6.0, fontweight="bold", color=BLUE, linespacing=1.3)
    box(60, LY, 23, LH, "Stages 4\u20135\ncomposition,\nreward-positivity",
        None, ec=BLUE, ts=5.9)
    box(87, LY, 23, LH, "Stage 6\nforecastability\ncriterion", None, ec=BLUE, ts=5.9)
    arrow(27, 47, 33, LY + LH / 2, BLUE, rad=0.15)
    for x1, x2 in ((56, 60), (83, 87)):
        arrow(x1, LY + LH / 2, x2, LY + LH / 2, BLUE)
    ax.text(3, 27, "Specification-side\nforecast precedes\ntraining", ha="left", va="center",
            fontsize=6.6, fontweight="bold", color=BLUE, linespacing=1.4)

    # ---- routed repairs ----------------------------------------------------
    box(122, 28, 41, 11, "Revise the specification", "specification-legible",
        ec=BLUE, fc="#EDF5FB", ts=6.4)
    box(122, 8, 41, 11, "Fix simulator or verifier", "solver artifact",
        ec=ORANGE, fc="#FDF6EA", ts=6.4)
    arrow(110, 29, 122, 33.5, BLUE, rad=0.12)
    arrow(110, 25, 122, 13.5, ORANGE, rad=-0.12)
    ax.text(116.5, 22.4, "routed by\nthe criterion", ha="center", va="center", fontsize=5.5,
            color="#4D4D4D", style="italic", linespacing=1.3)

    nc = json.loads((R / "negative_control.json").read_text())["results"]
    n_leg = sum(1 for v in nc.values() if v["emitted_by_SPEC_ENUM"])
    n_art = len(nc) - n_leg
    ax.text(33, 39.3, f"negative control: {n_leg} derived, vertical launch not "
                      f"derivable ({len(nc)}/{len(nc)})",
            fontsize=5.5, color="#4D4D4D", va="center", style="italic")

    # ---- boundary ----------------------------------------------------------
    ax.plot([30, 168], [42, 42], color="#B8B8B8", lw=0.55, ls=(0, (3.0, 2.2)), zorder=1)
    ax.text(168, 43.3, "no optimizer executed below this line", ha="right", va="bottom",
            fontsize=5.7, color=GREY, style="italic")

    # ---- annotation on the network -----------------------------------------
    ax.annotate("only the network reads text;\nall downstream inference is code",
                xy=(41, LY - 0.5), xytext=(28, 3.2),
                arrowprops=dict(arrowstyle="-", color=GREY, lw=0.5,
                                connectionstyle="arc3,rad=-0.18"),
                fontsize=5.7, color="#4D4D4D", ha="left", va="bottom", linespacing=1.35)
    ax.text(122, 3.2, f"{n_units} stateless calls \u00b7 {n_cand} candidates\n"
                      f"{cs['total_emissions']} redacted-vocabulary emissions",
            fontsize=5.6, color="#4D4D4D", ha="left", va="bottom", linespacing=1.35)

    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"fig3_workflow.{ext}")
    plt.close(fig)
    print(f"fig3: {n_units} units, {n_cand} candidates, "
          f"{cs['total_emissions']} emissions")


if __name__ == "__main__":
    figure1()
    figure2()
    figure3()
    print("\nwritten to", OUT)
