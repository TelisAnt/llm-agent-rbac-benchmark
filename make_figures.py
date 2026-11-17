"""Paper figures drawn from the CSV files written by authz_lab.evaluation.

    python make_figures.py                  # English labels, Wilson intervals -> figures/
    python make_figures.py --lang el        # Greek labels -> figures_el/
    python make_figures.py --ci bootstrap   # scenario bootstrap intervals instead of Wilson

fig_overall: ASR per model and configuration (one column wide)
fig_category: ASR per attack category (two columns)
fig_role: ASR per role (two columns)
fig_blocked: unauthorized calls proposed vs executed under RBAC (two columns)
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import Patch

COL_W, DBL_W = 3.5, 7.16  # IEEE column and page width, inches

# key, English label, fill colour (Paul Tol "muted"), hatch. The hatch keeps bars apart in greyscale.
CONFIGS = [("prompt_only", "Prompt-only", "#CC6677", ""),
           ("strict_schema", "Strict schema", "#DDCC77", "////"),
           ("rbac", "External RBAC", "#44AA99", "xxxx")]
TXT = {  # every string drawn inside the figures
    "en": {"cfg": {"prompt_only": "Prompt-only", "strict_schema": "Strict schema", "rbac": "External RBAC"},
           "cat": {"direct": "Direct", "indirect": "Indirect", "multistep": "Multi-step", "obfuscation": "Obfuscation"},
           "role": {"guest": "Guest", "analyst": "Analyst"},
           "ylab": "Attack success rate (%)", "ylab_blocked": "Unauthorized tool calls (% of attack runs)",
           "proposed": "Proposed by the model", "executed": "Executed after RBAC check",
           "panel": "abcdefgh"},
    "el": {"cfg": {"prompt_only": "Μόνο system prompt", "strict_schema": "Αυστηρά σχήματα", "rbac": "Εξωτερικό RBAC"},
           "cat": {"direct": "Άμεσο", "indirect": "Έμμεσο", "multistep": "Πολυβηματικό", "obfuscation": "Απόκρυψη"},
           "role": {"guest": "Επισκέπτης", "analyst": "Αναλυτής"},
           "ylab": "Ποσοστό επιτυχίας επιθέσεων (%)",
           "ylab_blocked": "Μη εξουσιοδοτημένες κλήσεις (% επιθετικών εκτελέσεων)",
           "proposed": "Προτάθηκαν από το μοντέλο", "executed": "Εκτελέστηκαν μετά τον έλεγχο RBAC",
           "panel": "αβγδεζηθ"},
}
T = TXT["en"]
MODEL_LABELS = {"ollama:llama3.1:8b": "Llama 3.1 8B", "ollama:qwen2.5:7b": "Qwen 2.5 7B"}


def setup_style() -> None:
    avail = {f.name for f in font_manager.fontManager.ttflist}
    family = next((f for f in ("Times New Roman", "Times", "Nimbus Roman", "STIXGeneral") if f in avail), "serif")
    if family != "Times New Roman":
        print(f"note: 'Times New Roman' not found, using '{family}' (metrically similar).")
    plt.rcParams.update({
        "font.family": "serif", "font.serif": [family], "mathtext.fontset": "stix",
        "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8.5, "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
        "axes.linewidth": 0.7, "xtick.direction": "in", "ytick.direction": "in",
        "xtick.major.width": 0.7, "ytick.major.width": 0.7, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "axes.grid": True, "axes.axisbelow": True, "axes.grid.axis": "y",
        "grid.color": "#B0B0B0", "grid.linewidth": 0.4, "grid.linestyle": ":",
        "hatch.linewidth": 0.5, "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 600,
    })


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def stat(row: dict | None, metric: str, ci: str):
    # returns (rate, lo, hi, n) with rates in percent, or None if the row has no such metric
    if row is None or not row.get(f"{metric}_rate"):
        return None
    tag = "wilson" if ci == "wilson" else "boot"
    return (100 * float(row[f"{metric}_rate"]), 100 * float(row[f"{metric}_{tag}_lo"]),
            100 * float(row[f"{metric}_{tag}_hi"]), int(row[f"{metric}_n"]))


def find(rows, **kw):
    return next((r for r in rows if all(r.get(k) == v for k, v in kw.items())), None)


def label_model(m: str) -> str:
    return MODEL_LABELS.get(m, m.split(":", 1)[-1])


def bars(ax, groups, series, get, annotate=False):
    # get(group_index, series_index) returns a stat() tuple or None
    width = 0.8 / len(series)
    x0 = np.arange(len(groups))
    for i, (_, color, hatch) in enumerate(series):
        xs, ys, lo, hi = [], [], [], []
        for g in range(len(groups)):
            s = get(g, i)
            if s is None:
                continue
            xs.append(x0[g] + (i - (len(series) - 1) / 2) * width)
            ys.append(s[0]); lo.append(max(0.0, s[0] - s[1])); hi.append(max(0.0, s[2] - s[0]))
        ax.bar(xs, ys, width * 0.92, color=color, edgecolor="black", linewidth=0.7, hatch=hatch, zorder=3)
        ax.errorbar(xs, ys, yerr=[lo, hi], fmt="none", ecolor="black", elinewidth=0.8,
                    capsize=2.2, capthick=0.8, zorder=4)
        for x, y, h in zip(xs, ys, hi):  # a zero bar is invisible, so label it
            if annotate or y == 0:
                ax.text(x, y + h + 1.5, f"{y:.0f}", ha="center", va="bottom", fontsize=6.5, zorder=5)
    ax.set_xticks(x0, groups)
    ax.set_xlim(-0.55, len(groups) - 0.45)
    ax.set_ylim(0, 105)
    ax.set_yticks(range(0, 101, 20))
    ax.tick_params(axis="x", length=0)


def legend_handles(series):
    return [Patch(facecolor=c, edgecolor="black", linewidth=0.7, hatch=h, label=l) for l, c, h in series]


def top_legend(fig, handles, ncol):
    leg = fig.legend(handles=handles, loc="upper center", ncol=ncol, frameon=True, fancybox=False,
                     edgecolor="black", framealpha=1, borderpad=0.4, handlelength=1.6, columnspacing=1.6,
                     bbox_to_anchor=(0.5, 1.0))
    leg.get_frame().set_linewidth(0.7)


def save(fig, outdir: Path, name: str):
    for ext in ("pdf", "png"):
        fig.savefig(outdir / f"{name}.{ext}", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print("wrote", outdir / f"{name}.pdf")


def panels(rows, models, key, order, labels, metric_rows_n, configs, ci, ylabel, outdir, name,
           annotate=False, series_override=None, fig_h=2.75):
    series = series_override or [(T["cfg"][k], c, h) for k, _, c, h in configs]
    fig, axes = plt.subplots(1, len(models), figsize=(DBL_W, fig_h), sharey=True, squeeze=False)
    for p, (ax, model) in enumerate(zip(axes[0], models)):
        def getter(g, i, model=model):
            if series_override:
                metric, cfg = series_override_spec[i]
                return stat(find(rows, model=model, config=cfg, **{key: order[g]}), metric, ci)
            return stat(find(rows, model=model, config=configs[i][0], **{key: order[g]}), "ASR", ci)
        n_ref = {g: next((int(r["ASR_n"]) for r in rows if r["model"] == model and r[key] == order[g]
                          and r.get("ASR_n") not in (None, "", "0")), None) for g in range(len(order))}
        ticks = [f"{labels[o]}\n($n$={n_ref[g]})" if n_ref[g] else labels[o] for g, o in enumerate(order)]
        bars(ax, ticks, series, getter, annotate)
        ax.set_title(f"({T['panel'][p]}) {label_model(model)}", loc="left", pad=3)
        if p == 0:
            ax.set_ylabel(ylabel)
    top_legend(fig, legend_handles(series), len(series))
    fig.tight_layout(rect=[0, 0, 1, 0.90], w_pad=1.0)
    save(fig, outdir, name)


series_override_spec: list = []  # filled in main() for the proposed-vs-executed figure


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", default="results", help="folder with the CSV files")
    ap.add_argument("--outdir", default=None, help="default: figures (en) or figures_el (el)")
    ap.add_argument("--lang", choices=("en", "el"), default="en", help="language of the text inside the figures")
    ap.add_argument("--ci", choices=("wilson", "bootstrap"), default="wilson")
    a = ap.parse_args()
    global T
    T = TXT[a.lang]
    res, out = Path(a.results), Path(a.outdir or ("figures" if a.lang == "en" else "figures_el"))
    out.mkdir(parents=True, exist_ok=True)
    setup_style()

    overall = read_csv(res / "by_model_config.csv")
    by_cat = read_csv(res / "by_category.csv")
    by_role = read_csv(res / "by_role.csv")
    models = sorted({r["model"] for r in overall})
    ci_name = "Wilson" if a.ci == "wilson" else "cluster-bootstrap"
    ylab = T["ylab"]

    # 1) overall, single column
    fig, ax = plt.subplots(figsize=(COL_W, 2.5))
    series = [(T["cfg"][k], c, h) for k, _, c, h in CONFIGS]
    bars(ax, [label_model(m) for m in models], series,
         lambda g, i: stat(find(overall, model=models[g], config=CONFIGS[i][0]), "ASR", a.ci), annotate=True)
    ax.set_ylabel(ylab)
    top_legend(fig, legend_handles(series), 3)
    fig.tight_layout(rect=[0, 0, 1, 0.88])
    save(fig, out, "fig_overall")

    # 2) by attack category
    cats = [c for c in T["cat"] if any(r["category"] == c for r in by_cat)]
    panels(by_cat, models, "category", cats, T["cat"], None, CONFIGS, a.ci, ylab, out, "fig_category")

    # 3) by role (attack roles only)
    roles = [r for r in T["role"] if any(x["role"] == r and x.get("ASR_n") not in ("", "0", None) for x in by_role)]
    panels(by_role, models, "role", roles, T["role"], None, CONFIGS, a.ci, ylab, out, "fig_role", fig_h=2.5)

    # 4) proposed vs executed under the RBAC configuration
    global series_override_spec
    series_override_spec = [("PropUnauth", "rbac"), ("ASR", "rbac")]
    panels(by_cat, models, "category", cats, T["cat"], None, CONFIGS, a.ci,
           T["ylab_blocked"], out, "fig_blocked", annotate=True,
           series_override=[(T["proposed"], "#BBBBBB", "...."), (T["executed"], "#44AA99", "xxxx")])
    print(f"Error bars: 95% {ci_name} intervals.")


if __name__ == "__main__":
    main()
