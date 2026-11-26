"""Train-only CUDA forward/backward probe; no optimizer and no fitted weights.

Reports compute-only lower bounds, not measured full-training throughput. AdamW,
host input preparation, logging, validation and persistence add time.
"""

import argparse
import math
import time
from pathlib import Path

import torch

from mim_llm.foundation.corpus import TokenDataset
from mim_llm.foundation.modeling import FoundationConfig, build_foundation
from mim_llm.foundation.objectives import make_batch, selected_ce
from mim_llm.foundation.plan import load_plan
from mim_llm.foundation.runner import order
from mim_llm.q3a.io import signature, write_json


def probe_batches(model, batches, *, device):
    initial = {k: p.detach().cpu().clone() for k, p in model.named_parameters()}
    model.train()
    results = []
    for index, batch in enumerate(batches):
        model.zero_grad(set_to_none=True)
        if device.startswith("cuda"):
            torch.cuda.synchronize()
        start = time.perf_counter()
        loss, targets = selected_ce(model, batch)
        if not torch.isfinite(loss):
            raise FloatingPointError("Nonfinite profiling loss")
        loss.backward()
        if device.startswith("cuda"):
            torch.cuda.synchronize()
        seconds = time.perf_counter() - start
        if not all(
            p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters()
        ):
            raise FloatingPointError("Nonfinite profiling gradient")
        results.append(
            {
                "index": index,
                "targets": targets,
                "input_tokens": int(batch["attention_mask"].sum()),
                "padded_positions": batch["input_ids"].numel(),
                "forward_backward_seconds": seconds,
                "ce_at_initialization": float(loss.detach()),
            }
        )
    unchanged = all(
        torch.equal(initial[k], p.detach().cpu()) for k, p in model.named_parameters()
    )
    if not unchanged:
        raise AssertionError("Profiling changed a learned weight")
    model.zero_grad(set_to_none=True)
    return {
        "optimizer_updates": 0,
        "learned_parameters_unchanged": unchanged,
        "batches": results,
        "targets": sum(r["targets"] for r in results),
        "seconds": sum(r["forward_backward_seconds"] for r in results),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA probe required; do not substitute CPU speed")
    if Path(args.output).exists():
        raise FileExistsError(args.output)
    plan = load_plan(args.plan)
    config = plan["config"]
    torch.set_num_threads(2)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    reports = []
    for kind, info in plan["models"].items():
        torch.manual_seed(0)
        model = build_foundation(FoundationConfig(**info["config"])).to("cuda")
        for stage_index, stage in enumerate(config["stages"]):
            data = TokenDataset(plan["data_dir"], "train", stage["name"])
            indices = order(len(data), 0, stage_index, 0)[: 32 * config["batch_size"]]

            def batches(data=data, indices=indices):
                for start in range(0, len(indices), config["batch_size"]):
                    yield make_batch(
                        [
                            data[i]
                            for i in indices[start : start + config["batch_size"]]
                        ],
                        pad_id=config["pad_id"],
                        context=config["context"],
                        device="cuda",
                    )

            # Two warm-up backward passes are also nonupdating and reported.
            warmed = probe_batches(
                model, [next(batches()), next(batches())], device="cuda"
            )
            torch.cuda.reset_peak_memory_stats()
            measured = probe_batches(model, batches(), device="cuda")
            speed = measured["targets"] / measured["seconds"]
            if not math.isfinite(speed) or speed <= 0:
                raise ValueError("Invalid throughput")
            reports.append(
                {
                    "kind": kind,
                    "stage": stage["name"],
                    "selection": "first32batches of declared seed0/stage0-or1/epoch0 order, train only",
                    "sample_indices_sha256": signature(indices),
                    "warmup_nonupdating_batches": len(warmed["batches"]),
                    **measured,
                    "forward_backward_targets_per_second": speed,
                    "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                    "optimistic_full_stage_forward_backward_seconds": stage["targets"]
                    / speed,
                }
            )
        del model
        torch.cuda.empty_cache()
    result = {
        "plan_id": plan["plan_id"],
        "gpu": torch.cuda.get_device_name(),
        "torch": str(torch.__version__),
        "precision": "float32_TF32_disabled",
        "test_or_validation_profiled": False,
        "optimizer_updates": 0,
        "reports": reports,
        "scope": "short random-initialization train-only forward/backward compute probe; excludes AdamW/host/logging/validation/Drive and does not establish final training duration or scientific quality",
    }
    write_json(args.output, result)
    print(__import__("json").dumps(result), flush=True)


if __name__ == "__main__":
    main()
