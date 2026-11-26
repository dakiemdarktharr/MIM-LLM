"""Fourteen additional fixed validation prefixes; no training or human labels."""

import argparse
import json
import re
from pathlib import Path

import torch

from mim_llm.generate import generate
from mim_llm.q3a.evaluate import load_q3a_checkpoint
from mim_llm.q3a.io import sha256, source_sha256, write_json, write_rows
from mim_llm.q3a.plan import load_plan
from mim_llm.shared_data import general_rows
from mim_llm.tokenizer import ByteTokenizer


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", required=True)
    p.add_argument("--checkpoint-root", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    torch.set_num_threads(2)
    plan = load_plan(a.plan)
    c = plan["config"]
    tokenizer = ByteTokenizer()
    output = Path(a.output)
    if output.exists() or output.with_suffix(".prompts.json").exists():
        raise FileExistsError(output)
    eligible = []
    for row in sorted(general_rows(plan["warmup"]), key=lambda r: r["source_id"]):
        if row["split"] != "validation" or '"' in row["text"] or "..." in row["text"]:
            continue
        parts = re.findall(r"[^.!?]+[.!?]", row["text"])
        if len(parts) < 4 or any(len(s.split()) < 3 for s in parts[:2]):
            continue
        prompt = (
            " ".join(s.strip() for s in parts[:2])
            + "\nContinue this story in three to five sentences.\nContinuation:\n"
        )
        if (
            len(tokenizer.encode(prompt, bos=True)) + c["decoding"]["max_new_tokens"]
            > c["context"]
        ):
            continue
        eligible.append({"source_id": row["source_id"], "prompt": prompt})
        if len(eligible) == 16:
            break
    if len(eligible) != 16:
        raise ValueError("Need sixteen eligible validation sources; no test fallback")
    prompts = eligible[2:]
    # Persist selection before generating or inspecting any new output.
    write_json(
        output.with_suffix(".prompts.json"),
        {
            "plan_id": plan["plan_id"],
            "selection": "Eligible validation sources 3..16 by source ID; same rule as original inspection",
            "prompts": prompts,
            "test_access": False,
            "decoding": c["decoding"],
            "source_sha256": source_sha256(__file__),
        },
    )
    rows = []
    for kind in c["backbones"]:
        identifier = f"warmup-{kind}-s0"
        path = Path(a.checkpoint_root) / identifier / "final.pt"
        model, checkpoint = load_q3a_checkpoint(path, plan, "cuda")
        declared = next(r for r in plan["runs"] if r["id"] == identifier)
        if (
            checkpoint["run"] != declared
            or not checkpoint["complete"]
            or checkpoint["stats"]["trained_targets"] != declared["targets"]
        ):
            raise ValueError("Require complete declared warm-up")
        for prompt in prompts:
            sample = generate(
                model,
                tokenizer,
                prompt["prompt"],
                device="cuda",
                max_new_tokens=c["decoding"]["max_new_tokens"],
                temperature=c["decoding"]["temperature"],
                top_k=c["decoding"]["top_k"],
                seed=c["decoding"]["seeds"][0],
            )
            rows.append(
                {
                    **prompt,
                    **sample,
                    "run_id": identifier,
                    "checkpoint_sha256": sha256(path),
                    "plan_id": plan["plan_id"],
                    "human_label": None,
                    "primary_evaluation": False,
                    "split": "validation_inspection",
                }
            )
        print(
            json.dumps({"run_id": identifier, "samples_saved": len(prompts)}),
            flush=True,
        )
        del model
        torch.cuda.empty_cache()
    write_rows(output, rows)
    print(
        json.dumps(
            {"output": str(output), "sha256": sha256(output), "samples": len(rows)}
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
