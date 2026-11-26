"""Post-hoc, read-only validation NLL diagnosis after failed writing calibration.

Reuses all sixteen previously selected prefixes. No generation, optimizer,
test performance measurement or human labels. Condition changes also change
positions/format, so this is not a causal proof of semantic memory.
"""

import argparse
import json
import re
from pathlib import Path

import torch

from mim_llm.models import parameter_count
from mim_llm.q3a.evaluate import load_q3a_checkpoint
from mim_llm.q3a.io import read_rows, sha256, source_sha256, write_json
from mim_llm.q3a.objectives import batch_examples, ce_loss, encode_example
from mim_llm.q3a.plan import load_plan
from mim_llm.shared_data import general_rows

SUFFIX = "\nContinue this story in three to five sentences.\nContinuation:\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--checkpoint-root", required=True)
    parser.add_argument("--inspection", action="append", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if Path(args.output).exists():
        raise FileExistsError(args.output)
    torch.set_num_threads(2)
    plan = load_plan(args.plan)
    selected = {}
    for file in args.inspection:
        for row in read_rows(file):
            if row["plan_id"] != plan["plan_id"] or row["primary_evaluation"]:
                raise ValueError("Require original calibration inspection")
            source = row.get("source_id")
            if source:
                if source in selected and selected[source] != row["prompt"]:
                    raise ValueError("Different prompts for the same source")
                selected[source] = row["prompt"]
    if len(selected) != 16:
        raise ValueError("Retain exactly the sixteen prior validation prefixes")
    validation = {
        r["source_id"]: r
        for r in general_rows(plan["warmup"])
        if r["split"] == "validation"
    }
    rows, identities = [], {}
    with torch.inference_mode():
        for kind in ("mingru", "transformer"):
            run_id = f"warmup-{kind}-s0"
            checkpoint_path = Path(args.checkpoint_root) / run_id / "final.pt"
            model, checkpoint = load_q3a_checkpoint(checkpoint_path, plan, "cpu")
            declared = next(r for r in plan["runs"] if r["id"] == run_id)
            if (
                checkpoint["run"] != declared
                or not checkpoint["complete"]
                or checkpoint["stats"]["trained_targets"] != declared["targets"]
            ):
                raise ValueError("Require completed declared warm-up")
            model.eval()
            identities[kind] = {
                "checkpoint_sha256": sha256(checkpoint_path),
                "actual_parameters": parameter_count(model),
            }
            for source, prompt in sorted(selected.items()):
                parts = re.findall(r"[^.!?]+[.!?]", validation[source]["text"])
                prefix = " ".join(p.strip() for p in parts[:2])
                if len(parts) < 4 or prompt != prefix + SUFFIX:
                    raise ValueError("Prior prefix differs from original validation")
                response = " ".join(p.strip() for p in parts[2:5])
                for condition, context in {
                    "prefix_and_instruction": prompt,
                    "instruction_only": SUFFIX,
                    "prefix_only": prefix + " ",
                }.items():
                    encoded = encode_example(
                        context, response, plan["config"]["context"]
                    )
                    # Exclude synthetic early EOS on a possibly truncated reference.
                    encoded["targets"][-1] = -100
                    batch = batch_examples([encoded], plan["config"]["context"])
                    loss, targets = ce_loss(model, batch)
                    if not torch.isfinite(loss) or targets != len(
                        response.encode("utf-8")
                    ):
                        raise ValueError("Invalid response NLL or shifted label count")
                    rows.append(
                        {
                            "kind": kind,
                            "source_id": source,
                            "condition": condition,
                            "ce": float(loss),
                            "targets_excluding_eos": targets,
                            "context_bytes": len(context.encode("utf-8")),
                        }
                    )
            del model
    summaries = {}
    for kind in identities:
        summaries[kind] = {}
        for condition in ("prefix_and_instruction", "instruction_only", "prefix_only"):
            subset = [
                r for r in rows if r["kind"] == kind and r["condition"] == condition
            ]
            summaries[kind][condition] = {
                "stories": len(subset),
                "source_mean_ce": sum(r["ce"] for r in subset) / len(subset),
                "target_weighted_ce": sum(
                    r["ce"] * r["targets_excluding_eos"] for r in subset
                )
                / sum(r["targets_excluding_eos"] for r in subset),
            }
    report = {
        "plan_id": plan["plan_id"],
        "source_sha256": source_sha256(__file__),
        "torch": torch.__version__,
        "device": "cpu",
        "identities": identities,
        "inspection_sha256": {str(p): sha256(p) for p in args.inspection},
        "selection": "All sixteen prior calibration prefixes; post-hoc diagnosis",
        "optimizer_updates": 0,
        "generation_calls": 0,
        "test_performance_measured": False,
        "human_labels": False,
        "caveat": "Format/position changes are confounded; not semantic-memory proof or primary evaluation",
        "summaries": summaries,
        "rows": rows,
    }
    write_json(args.output, report)
    print(json.dumps({"summaries": summaries, "diagnostic_rows": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
