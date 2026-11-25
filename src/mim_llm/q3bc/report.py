"""Generate manuscript assets only from supplied final-test human analyses."""

from pathlib import Path

from ..q3a.io import read_json


def results_table(analysis, output):
    a = read_json(analysis)
    if a.get("split") != "test" or not a.get("primary_results"):
        raise ValueError("Real final-test analysis required; leave results blank")
    rows = [r for r in a["primary_results"] if r["primary"]]
    if {r["backbone"] for r in rows} != {"mingru", "transformer"} or not all(
        r["all_three_seeds"] for r in rows
    ):
        raise ValueError(
            "Both backbones and three seeds required for this manuscript table"
        )
    lines = [
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        r"Backbone & Difference & Lower 95\% & Upper 95\% \\",
        r"\midrule",
    ]
    for r in rows:
        lines.append(
            f"{r['backbone']} & {r['effect']:.4f} & {r['ci95'][0]:.4f} & {r['ci95'][1]:.4f} "
            + r"\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}"]
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
