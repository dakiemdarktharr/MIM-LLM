"""Post-training only. A owns the six shared warm-ups; no duplicate pretraining."""

from __future__ import annotations

import json
import time
from pathlib import Path

import torch

from ..models import ModelConfig, build_model, parameter_count
from ..q3a.io import read_rows, sha256, write_json
from ..q3a.runner import (
    atomic_checkpoint,
    restore_checkpoint,
    take_batch,
    validation_loss,
)
from ..training_gate import require_training_permission
from .objectives import examples_for, loss_batch, validation_examples
from .plan import load_plan


def execute(
    plan_path,
    run_id,
    output_root,
    *,
    seconds_limit,
    device="cpu",
    resume=False,
    warmup_root=None,
):
    require_training_permission("model", run_id)
    plan = load_plan(plan_path, require_bank=True)
    require_training_permission("model", run_id, plan_id=plan["plan_id"])
    if seconds_limit <= 0:
        raise ValueError("Explicit positive invocation time cap required")
    run = next((r for r in plan["runs"] if r["id"] == run_id), None)
    if run is None:
        raise ValueError(
            "Only the 24 post-training IDs are in this plan; use the shared A plan for warm-up"
        )
    c = plan["config"]
    torch.manual_seed(run["seed"])
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(run["seed"])
    model_config = ModelConfig(**plan["models"][run["kind"]]["config"])
    model = build_model(model_config).to(device)
    parent_path = Path(warmup_root or output_root) / run["parent"] / "final.pt"
    parent = torch.load(parent_path, map_location="cpu", weights_only=True)
    if (
        parent["plan_id"] != plan["shared_plan_id"]
        or not parent["complete"]
        or parent["run"]["id"] != run["parent"]
    ):
        raise ValueError("Wrong/incomplete shared initialization")
    if parent["stats"]["trained_targets"] != parent["run"]["targets"]:
        raise ValueError("Incomplete warm-up target budget")
    model.load_state_dict(parent["model"])
    parent_sha = sha256(parent_path)
    examples = examples_for(plan, run)
    valid = validation_examples(plan)
    if plan["study"] == "c" and any(
        x["frozen_learner_sha256"] != parent_sha for x in examples
    ):
        raise ValueError(
            "History bank is not tied to this exact learner initialization"
        )
    out = Path(output_root) / run_id
    if out.exists() and any(out.iterdir()) and not resume:
        raise FileExistsError(out)
    out.mkdir(parents=True, exist_ok=True)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=c["learning_rate"], weight_decay=c["weight_decay"]
    )
    identity = {
        "plan_id": plan["plan_id"],
        "run": run,
        "parent_sha256": parent_sha,
        "device_type": torch.device(device).type,
        "batch_size": c["batch_size"],
        "precision": "float32",
    }
    stats = {
        "trained_targets": 0,
        "processed_input_tokens": 0,
        "event_targets": 0,
        "answer_targets": 0,
        "probe_input_tokens": 0,
        "probe_prefix_bytes": 0,
        "semantic_write_sum": 0,
        "updates": 0,
        "epoch": 0,
        "cursor": 0,
        "train_seconds": 0.0,
        "validation_seconds": 0.0,
        "best_validation_ce": float("inf"),
    }
    if resume:
        saved = restore_checkpoint(
            out / "latest.pt", model, optimizer, expected=identity
        )
        stats = saved["stats"]
        if (out / "metrics.jsonl").exists():
            events = read_rows(out / "metrics.jsonl")
            discarded = [x for x in events if x["update"] > stats["updates"]]
            if discarded:
                with (out / "metrics.jsonl").open("w", encoding="utf-8") as f:
                    for x in events:
                        if x["update"] <= stats["updates"]:
                            f.write(json.dumps(x) + "\n")
                with (out / "replayed-work.jsonl").open("a", encoding="utf-8") as f:
                    for x in discarded:
                        f.write(json.dumps(x) + "\n")
    if device.startswith("cuda"):
        torch.cuda.reset_peak_memory_stats()
    start = time.perf_counter()

    def checkpoint(complete=False):
        return {
            "config": vars(model_config),
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "identity": identity,
            "plan_id": plan["plan_id"],
            "run": run,
            "stats": dict(stats),
            "complete": complete,
            "parent_sha256": parent_sha,
            "rng_cpu": torch.get_rng_state(),
            "rng_cuda": torch.cuda.get_rng_state_all()
            if torch.cuda.is_available()
            else None,
        }

    if not resume:
        atomic_checkpoint(out / "latest.pt", checkpoint())
    try:
        while (
            stats["trained_targets"] < run["targets"]
            and time.perf_counter() - start < seconds_limit
        ):
            tic = time.perf_counter()
            model.train()
            optimizer.zero_grad(set_to_none=True)
            items, epoch, cursor = take_batch(
                examples, run["seed"], stats["epoch"], stats["cursor"], c["batch_size"]
            )
            loss, n, extra = loss_batch(
                model,
                items,
                plan,
                run,
                remaining=run["targets"] - stats["trained_targets"],
                device=device,
            )
            if n < 1 or not torch.isfinite(loss):
                raise FloatingPointError("Invalid loss/target count")
            loss.backward()
            norm = torch.nn.utils.clip_grad_norm_(
                model.parameters(), c["grad_clip"], error_if_nonfinite=True
            )
            optimizer.step()
            if device.startswith("cuda"):
                torch.cuda.synchronize()
            elapsed = time.perf_counter() - tic
            stats["epoch"] = epoch
            stats["cursor"] = cursor
            stats["trained_targets"] += n
            stats["updates"] += 1
            stats["train_seconds"] += elapsed
            for key, value in extra.items():
                stats[key] += value
            with (out / "metrics.jsonl").open("a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "update": stats["updates"],
                            "targets": stats["trained_targets"],
                            "objective": float(loss.detach()),
                            "gradient_norm": float(norm),
                            "seconds": elapsed,
                            **extra,
                        }
                    )
                    + "\n"
                )
            if (
                stats["updates"] % c["checkpoint_every_updates"] == 0
                or stats["trained_targets"] == run["targets"]
            ):
                tic = time.perf_counter()
                v = validation_loss(model, valid, c["context"], c["batch_size"], device)
                if device.startswith("cuda"):
                    torch.cuda.synchronize()
                stats["validation_seconds"] += time.perf_counter() - tic
                improved = v["ce"] < stats["best_validation_ce"]
                if improved:
                    stats["best_validation_ce"] = v["ce"]
                saved = checkpoint()
                atomic_checkpoint(out / "latest.pt", saved)
                if improved:
                    atomic_checkpoint(out / "best.pt", saved)
        complete = stats["trained_targets"] == run["targets"]
        atomic_checkpoint(out / "latest.pt", checkpoint(complete))
        if complete:
            atomic_checkpoint(out / "final.pt", checkpoint(True))
    except BaseException:
        write_json(
            out / "interruption.json",
            {
                "last_checkpoint_sha256": sha256(out / "latest.pt"),
                "uncheckpointed_work_may_be_replayed": True,
                "elapsed_invocation": time.perf_counter() - start,
            },
            replace=True,
        )
        raise
    result = {
        "plan_id": plan["plan_id"],
        "run": run,
        "stats": stats,
        "complete": complete,
        "actual_parameters": parameter_count(model),
        "device": device,
        "gpu_name": torch.cuda.get_device_name() if device.startswith("cuda") else None,
        "parent_sha256": parent_sha,
        "invocation_seconds": time.perf_counter() - start,
        "precision": "float32",
        "peak_allocated_bytes": torch.cuda.max_memory_allocated()
        if device.startswith("cuda")
        else None,
        "peak_reserved_bytes": torch.cuda.max_memory_reserved()
        if device.startswith("cuda")
        else None,
        "flop_proxy": 6 * parameter_count(model) * stats["processed_input_tokens"],
        "flop_proxy_excludes": "quadratic attention, optimizer, validation and generation; probe inputs already included once",
    }
    write_json(out / "run.json", result, replace=True)
    return result
