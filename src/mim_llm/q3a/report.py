"""Export only supplied test-label analyses; never fill missing results."""

from pathlib import Path

from .io import read_json


def results_table(analysis_path, output):
    analysis = read_json(analysis_path)
    if analysis.get("split") != "test" or not analysis.get("primary_results"):
        raise ValueError(
            "A real adjudicated test analysis is required; leave draft results empty"
        )
    if not analysis.get("all_three_training_seeds_present"):
        raise ValueError(
            "All declared training seeds required for this manuscript table"
        )
    if {r["backbone"] for r in analysis["primary_results"]} != {
        "mingru",
        "transformer",
    }:
        raise ValueError("Both declared backbones required for this manuscript table")
    lines = [
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        r"Backbone & A1--A2 & Lower 95\% & Upper 95\% \\",
        r"\midrule",
    ]
    for row in analysis["primary_results"]:
        name = row["backbone"]
        if name not in ("mingru", "transformer"):
            raise ValueError("Unexpected backbone label")
        lines.append(
            f"{name} & {row['effect']:.4f} & {row['ci95'][0]:.4f} & {row['ci95'][1]:.4f} "
            + r"\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}"]
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def transfer_template(output):
    """A blank schema for genuinely licensed/audited external scenarios."""
    from .io import write_json

    write_json(
        output,
        {
            "status": "blank_not_data",
            "sources": [],
            "required_source_fields": [
                "source_id",
                "source_url",
                "license",
                "license_url",
                "source_hash",
                "split",
                "original_text",
                "adapted_scenarios",
                "adaptation_description",
                "reviewer_ids",
            ],
            "requirements": [
                "No training/selection source overlap",
                "No invented human authorship or review",
                "Validate semantic interventions and ambiguous/omitted facts",
                "Register before final test; report separately from controlled templates",
            ],
        },
    )
