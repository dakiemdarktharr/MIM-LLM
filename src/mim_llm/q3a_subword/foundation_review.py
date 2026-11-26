"""Fixed foundation writing review, separate from the locked primary test.

Preparation does not create a model. Generation requires BOTH completed
foundation parents and retains every declared sample, including empty outputs.
"""

import hashlib
import re
from pathlib import Path

import torch

from ..foundation.codec import FrozenTokenizer
from ..foundation.modeling import FoundationConfig, build_foundation
from ..foundation.plan import load_plan
from ..q3a.io import read_json, read_rows, sha256, signature, source_sha256, write_json
from . import inference
from .inference import generate


def fixed_prompts(recipe, rows):
    """Reconstruct the SAME sixteen validation prefixes; never fall back to test."""
    selected = recipe["sources"]
    if len(selected) != 16 or len({r["source_id"] for r in selected}) != 16:
        raise ValueError("Require the sixteen distinct historical source IDs")
    wanted = {r["source_id"] for r in selected}
    originals = {}
    for row in rows:
        if row["source_id"] in wanted:
            if row["split"] != "validation" or row["source_id"] in originals:
                raise ValueError("Historical review requires unique validation sources")
            originals[row["source_id"]] = row
    if set(originals) != wanted:
        raise ValueError("Missing historical validation source; no test fallback")
    suffix = "\nContinue this story in three to five sentences.\nContinuation:\n"
    prompts = []
    for item in selected:
        parts = re.findall(r"[^.!?]+[.!?]", originals[item["source_id"]]["text"])
        prompt = " ".join(p.strip() for p in parts[:2]) + suffix
        if hashlib.sha256(prompt.encode()).hexdigest() != item["prompt_sha256"]:
            raise ValueError("Historical validation prompt changed")
        prompts.append(
            {
                "source_id": item["source_id"],
                "condition": "conditional",
                "prompt": prompt,
            }
        )
    prompts.append(
        {
            "source_id": None,
            "condition": "unconditional",
            "prompt": "Write a short story in three sentences.\nContinuation:\n",
        }
    )
    return prompts


def prepare_review(plan_path, recipe_path, corpus, output):
    plan = load_plan(plan_path)
    if sha256(corpus) != plan["corpus_sha256"]:
        raise ValueError("Wrong foundation corpus")
    prompts = fixed_prompts(read_json(recipe_path), read_rows(corpus))
    tokenizer = FrozenTokenizer(plan["tokenizer"], plan["tokenizer_spec"])
    decoding = plan["config"]["decoding"]
    for row in prompts:
        if (
            len(tokenizer.encode(row["prompt"], bos=True)) + decoding["max_new_tokens"]
            > plan["config"]["context"]
        ):
            raise ValueError("Review prompt exceeds context; do not truncate/drop")
    value = {
        "purpose": "fixed validation writing feasibility, not primary Q3-A evaluation",
        "plan_id": plan["plan_id"],
        "corpus_sha256": plan["corpus_sha256"],
        "recipe_sha256": sha256(recipe_path),
        "tokenizer_sha256": plan["tokenizer_spec"]["sha256"],
        "decoding": decoding,
        "prompts": prompts,
        "expected_samples": 2 * len(prompts),
        "human_labels": False,
        "test_performance_measured": False,
        "source_sha256": source_sha256(__file__),
        "inference_backend": inference.BACKEND,
        "inference_source_sha256": source_sha256(inference.__file__),
    }
    value["review_id"] = signature(value)
    write_json(output, value)
    return value


def check_complete_parent(checkpoint, plan, run):
    identity = checkpoint.get("identity", {})
    stats = checkpoint.get("stats", {})
    if (
        identity.get("plan_id") != plan["plan_id"]
        or identity.get("run") != run
        or identity.get("precision") != "float32"
        or checkpoint.get("complete") is not True
        or stats.get("stage") != len(plan["config"]["stages"])
        or stats.get("stage_targets") != 0
        or stats.get("targets") != sum(s["targets"] for s in plan["config"]["stages"])
        or stats.get("updates", 0) < 1
    ):
        raise ValueError("Review requires the complete declared LM and SFT parent")


def verify_review(value, plan):
    payload = {k: v for k, v in value.items() if k != "review_id"}
    if signature(payload) != value.get("review_id"):
        raise ValueError("Changed writing review manifest")
    if (
        value["plan_id"] != plan["plan_id"]
        or value["corpus_sha256"] != plan["corpus_sha256"]
        or value["tokenizer_sha256"] != plan["tokenizer_spec"]["sha256"]
        or value["decoding"] != plan["config"]["decoding"]
        or value["source_sha256"] != source_sha256(__file__)
        or value.get("inference_backend") != inference.BACKEND
        or value.get("inference_source_sha256") != source_sha256(inference.__file__)
        or value["expected_samples"] != 34
        or len(value["prompts"]) != 17
    ):
        raise ValueError("Writing review does not match the declared foundation")


def generate_review(plan_path, manifest, checkpoint_root, output, *, device="cpu"):
    """Only private/local or Drive outputs; no automatic writing-success labels."""
    import json

    if device != "cpu":
        raise ValueError("Reviewed generation uses the canonical CPU/FP64 backend")
    plan = load_plan(plan_path)
    review = read_json(manifest)
    verify_review(review, plan)
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    if {r["kind"] for r in plan["runs"]} != {"mingru", "transformer"} or len(
        plan["runs"]
    ) != 2:
        raise ValueError("Both seed-zero foundation parents required")
    # Verify both parents BEFORE emitting any samples. Never treat partial LM
    # weights or an SFT-stage boundary receipt as a completed foundation.
    parents = []
    for run in plan["runs"]:
        path = Path(checkpoint_root) / run["id"] / "final.pt"
        value = torch.load(path, map_location="cpu", weights_only=True)
        check_complete_parent(value, plan, run)
        parents.append((run, path, sha256(path)))
        del value
    output.mkdir(parents=True)
    write_json(
        output / "started.json",
        {
            "review_id": review["review_id"],
            "plan_id": plan["plan_id"],
            "manifest_sha256": sha256(manifest),
            "device": device,
            "inference_backend": inference.BACKEND,
            "inference_source_sha256": source_sha256(inference.__file__),
            "checkpoint_sha256": {r["id"]: digest for r, _, digest in parents},
            "expected_samples": 34,
            "optimizer_updates": 0,
            "human_labels": False,
        },
    )
    tokenizer = FrozenTokenizer(plan["tokenizer"], plan["tokenizer_spec"])
    counts = {}
    # A failure leaves a flushed partial JSONL and no completed receipt.
    with (output / "samples.jsonl").open("x", encoding="utf-8", newline="\n") as handle:
        for run, path, digest in parents:
            saved = torch.load(path, map_location="cpu", weights_only=True)
            check_complete_parent(saved, plan, run)
            if sha256(path) != digest:
                raise ValueError("Parent checkpoint changed during review")
            model = (
                build_foundation(
                    FoundationConfig(**plan["models"][run["kind"]]["config"])
                )
                .double()
                .cpu()
            )
            model.load_state_dict(saved["model"], strict=True)
            del saved
            samples = []
            for prompt in review["prompts"]:
                sample = generate(
                    model,
                    tokenizer,
                    prompt["prompt"],
                    device=device,
                    **review["decoding"],
                )
                row = {
                    **prompt,
                    **sample,
                    "run_id": run["id"],
                    "checkpoint_sha256": digest,
                    "plan_id": plan["plan_id"],
                    "review_id": review["review_id"],
                    "actual_parameters": sum(p.numel() for p in model.parameters()),
                    "split": "validation_feasibility",
                }
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                handle.flush()
                samples.append(row)
            counts[run["id"]] = {
                "samples": len(samples),
                "distinct_conditional_outputs": len(
                    {
                        r["continuation"]
                        for r in samples
                        if r["condition"] == "conditional"
                    }
                ),
                "empty_outputs": sum(not r["continuation"].strip() for r in samples),
                "cap_reached": sum(r["cap_reached"] for r in samples),
                "eos_emitted": sum(r["eos_emitted"] for r in samples),
            }
            del model
            if device.startswith("cuda"):
                torch.cuda.empty_cache()
    result = {
        "complete": True,
        "samples": sum(r["samples"] for r in counts.values()),
        "by_run": counts,
        "samples_sha256": sha256(output / "samples.jsonl"),
        "review_id": review["review_id"],
        "human_labels": False,
        "primary_evaluation": False,
        "writing_gate_passed": None,
        "note": "Counts are diagnostics, not fluency/logic or human ratings; retain every sample.",
    }
    if result["samples"] != review["expected_samples"]:
        raise ValueError("Incomplete writing panel")
    write_json(output / "completed.json", result)
    return result
