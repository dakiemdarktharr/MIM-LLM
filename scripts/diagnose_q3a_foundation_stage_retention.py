"""Replay LM-boundary and complete foundation weights on identical validation.

Secondary stage-retention diagnostic only. Never changes the complete-parent
writing gate, optimizer, training schedule or locked general/controlled test.
"""

import argparse
import math
import random
import time
from datetime import UTC, datetime
from pathlib import Path

import torch

from mim_llm.foundation.codec import FrozenTokenizer
from mim_llm.foundation.corpus import TokenDataset
from mim_llm.foundation.modeling import FoundationConfig, build_foundation
from mim_llm.foundation.plan import load_plan
from mim_llm.q3a.io import read_rows, sha256, source_sha256, write_json
from mim_llm.q3a_subword import language_eval
from mim_llm.q3a_subword.foundation_review import check_complete_parent
from mim_llm.q3a_subword.inference import BACKEND, canonical_backend


def diagnose(plan_path, pre_path, post_path):
    plan = load_plan(plan_path)
    hashes = {"pre_sft": sha256(pre_path), "post_sft": sha256(post_path)}
    pre = torch.load(pre_path, map_location="cpu", weights_only=True)
    post = torch.load(post_path, map_location="cpu", weights_only=True)
    run = next(
        (r for r in plan["runs"] if r == post.get("identity", {}).get("run")), None
    )
    stages = plan["config"]["stages"]
    if run is None or len(stages) != 2 or [s["name"] for s in stages] != ["lm", "sft"]:
        raise ValueError("Require the declared two-stage foundation run")
    check_complete_parent(post, plan, run)
    if (
        pre.get("identity") != post["identity"]
        or pre.get("complete") is not False
        or pre["stats"]["stage"] != 0
        or pre["stats"]["stage_targets"] != stages[0]["targets"]
        or pre["stats"]["targets"] != stages[0]["targets"]
    ):
        raise ValueError(
            "Require the exact saved LM boundary, never arbitrary early selection"
        )
    if any(
        v.is_floating_point() and v.dtype != torch.float32
        for state in (pre["model"], post["model"])
        for v in state.values()
    ):
        raise ValueError("Original trained tensors must remain FP32")
    tokenizer = FrozenTokenizer(plan["tokenizer"], plan["tokenizer_spec"])
    data = TokenDataset(plan["data_dir"], "validation", "lm")
    sources = read_rows(Path(plan["data_dir"]) / "validation-lm.sources.jsonl")
    if len(sources) != len(data):
        raise ValueError("Wrong validation source index")
    cfg = FoundationConfig(**plan["models"][run["kind"]]["config"])
    model = build_foundation(cfg, seed=run["seed"]).double().cpu()
    counts, results = [], {}
    with canonical_backend(), torch.inference_mode():
        for name, saved in (("pre_sft", pre), ("post_sft", post)):
            model.load_state_dict(saved["model"], strict=True)
            started = time.perf_counter()
            results[name] = language_eval.summarize_language(
                model,
                ((sources[i]["source_id"], data[i]) for i in range(len(data))),
                pad_id=tokenizer.pad_id,
                context=cfg.context,
                batch_size=plan["config"]["batch_size"],
                device="cpu",
                draws=2000,
            )
            results[name]["evaluation_seconds"] = time.perf_counter() - started
            counts.append(sum(p.numel() for p in model.parameters()))
    if counts != [plan["models"][run["kind"]]["actual_parameters"]] * 2:
        raise ValueError("Actual parameter count differs")
    before, after = [
        {r["source_id"]: r for r in results[name]["per_source"]}
        for name in ("pre_sft", "post_sft")
    ]
    if set(before) != set(after) or any(
        before[k]["targets"] != after[k]["targets"] for k in before
    ):
        raise ValueError("Stage comparison must use identical source targets")
    pairs = [
        {
            "source_id": k,
            "targets": before[k]["targets"],
            "delta_nll_sum": after[k]["nll_sum_nats"] - before[k]["nll_sum_nats"],
        }
        for k in sorted(before)
    ]
    rng = random.Random(2026)
    draws = []
    for _ in range(2000):
        sampled = rng.choices(pairs, k=len(pairs))
        draws.append(
            sum(r["delta_nll_sum"] for r in sampled)
            / sum(r["targets"] for r in sampled)
        )
    draws.sort()
    if hashes != {"pre_sft": sha256(pre_path), "post_sft": sha256(post_path)}:
        raise ValueError("Checkpoint changed during read-only replay")
    return {
        "utc": datetime.now(UTC).isoformat(),
        "purpose": "secondary paired stage-retention validation diagnostic",
        "plan_id": plan["plan_id"],
        "run": run,
        "actual_parameters": counts[0],
        "checkpoint_sha256": hashes,
        "pre_training_targets": pre["stats"]["targets"],
        "post_training_targets": post["stats"]["targets"],
        "stages": results,
        "post_minus_pre_nll_nats_per_target": sum(r["delta_nll_sum"] for r in pairs)
        / sum(r["targets"] for r in pairs),
        "paired_source_ci95": [draws[int(0.025 * 1999)], draws[int(0.975 * 1999)]],
        "bootstrap_draws": 2000,
        "bootstrap_seed": 2026,
        "uncertainty_scope": "source sampling conditional on this one initialization and its two observed stages; no matched continued-LM control or across-seed causal claim",
        "split": "validation",
        "targets_equal": True,
        "EOS_supervised": True,
        "device": "cpu",
        "precision": "float64",
        "inference_backend": BACKEND,
        "torch": str(torch.__version__),
        "optimizer_updates": 0,
        "test_access": False,
        "tokenizer_sha256": plan["tokenizer_spec"]["sha256"],
        "encoded_manifest_sha256": plan["data_manifest_sha256"],
        "implementation_sha256": source_sha256(__file__),
        "language_eval_source_sha256": source_sha256(language_eval.__file__),
        "writing_gate_changed": False,
        "writing_or_logic_measured": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("plan", "pre-sft-checkpoint", "complete-checkpoint", "output"):
        parser.add_argument("--" + name, required=True)
    a = parser.parse_args()
    if Path(a.output).exists():
        raise FileExistsError(a.output)
    result = diagnose(a.plan, a.pre_sft_checkpoint, a.complete_checkpoint)
    if not math.isfinite(result["post_minus_pre_nll_nats_per_target"]):
        raise FloatingPointError("Nonfinite stage comparison")
    write_json(a.output, result)
    print({k: v for k, v in result.items() if k != "stages"})


if __name__ == "__main__":
    main()
