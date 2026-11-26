"""Read-only validation writing/PPL inspection after completed Q3-A warm-ups.

No optimizer, tokenizer fitting, final-test access or fabricated human labels.
The six samples are a feasibility inspection, not a primary paper evaluation.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import torch

from mim_llm.generate import generate
from mim_llm.models import parameter_count
from mim_llm.q3a.evaluate import load_q3a_checkpoint
from mim_llm.q3a.io import sha256, source_sha256, write_json, write_rows
from mim_llm.q3a.plan import load_plan
from mim_llm.q3a.runner import language_examples, validation_loss
from mim_llm.shared_data import general_rows
from mim_llm.tokenizer import ByteTokenizer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--checkpoint-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    output = Path(args.output)
    metadata = output.with_suffix(".meta.json")
    if output.exists() or metadata.exists():
        raise FileExistsError("Use a new inspection output path")
    torch.set_num_threads(2)
    plan = load_plan(args.plan)
    c = plan["config"]
    tokenizer = ByteTokenizer()
    general = general_rows(plan["warmup"])
    prompts = [
        {
            "purpose": "learned_general_format",
            "source_id": None,
            "prompt": "Write a short story in three sentences.\nContinuation:\n",
        }
    ]
    for row in sorted(general, key=lambda r: r["source_id"]):
        if row["split"] != "validation" or '"' in row["text"] or "..." in row["text"]:
            continue
        parts = re.findall(r"[^.!?]+[.!?]", row["text"])
        if len(parts) < 4 or any(len(p.split()) < 3 for p in parts[:2]):
            continue
        prompt = (
            " ".join(p.strip() for p in parts[:2])
            + "\nContinue this story in three to five sentences.\nContinuation:\n"
        )
        if (
            len(tokenizer.encode(prompt, bos=True)) + c["decoding"]["max_new_tokens"]
            > c["context"]
        ):
            continue
        prompts.append(
            {
                "purpose": "heldout_validation_prefix",
                "source_id": row["source_id"],
                "prompt": prompt,
            }
        )
        if len(prompts) == 3:
            break
    if len(prompts) != 3:
        raise ValueError("Need two eligible validation sources; no test fallback")
    results, summaries = [], []
    started = time.perf_counter()
    for kind in c["backbones"]:
        run_id = f"warmup-{kind}-s0"
        path = Path(args.checkpoint_root) / run_id / "final.pt"
        model, checkpoint = load_q3a_checkpoint(path, plan, args.device)
        declared = next(r for r in plan["runs"] if r["id"] == run_id)
        if (
            checkpoint["run"] != declared
            or checkpoint["complete"] is not True
            or checkpoint["stats"]["trained_targets"] != declared["targets"]
        ):
            raise ValueError("Require complete declared seed-0 shared initialization")
        identity = {
            "run_id": run_id,
            "checkpoint_sha256": sha256(path),
            "actual_parameters": parameter_count(model),
            "plan_id": plan["plan_id"],
        }
        ppl = validation_loss(
            model,
            language_examples(general, "validation", c["context"]),
            c["context"],
            c["batch_size"],
            args.device,
        )
        summaries.append({**identity, "general_validation_original_stories_only": ppl})
        print(json.dumps(summaries[-1]), flush=True)
        for prompt in prompts:
            sample = generate(
                model,
                tokenizer,
                prompt["prompt"],
                device=args.device,
                max_new_tokens=c["decoding"]["max_new_tokens"],
                temperature=c["decoding"]["temperature"],
                top_k=c["decoding"]["top_k"],
                seed=c["decoding"]["seeds"][0],
            )
            result = {
                **identity,
                **prompt,
                **sample,
                "split": "validation_inspection",
                "human_label": None,
                "primary_evaluation": False,
            }
            results.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
        del model
        if args.device.startswith("cuda"):
            torch.cuda.empty_cache()
    write_rows(output, results)
    write_json(
        metadata,
        {
            "plan_id": plan["plan_id"],
            "inspection_source_sha256": source_sha256(__file__),
            "generations_sha256": sha256(output),
            "prompt_selection": "Fixed general-format prompt and first two eligible source-ID-sorted original validation prefixes, chosen before observing outputs",
            "human_labels": False,
            "primary_evaluation": False,
            "test_access": False,
            "review_status": "qualitative_review_pending_not_primary_labels",
            "elapsed_seconds": time.perf_counter() - started,
            "summaries": summaries,
        },
    )
    print("INSPECTION_OUTPUT", output, flush=True)


if __name__ == "__main__":
    main()
