"""Exact exposure, stage boundaries, logs and resumable float32 AdamW training."""

import json
import math
import os
import platform
import random
import time
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

import torch

from ..q3a.io import read_rows, sha256
from ..training_gate import require_training_permission
from .corpus import TokenDataset
from .modeling import FoundationConfig, build_foundation
from .objectives import make_batch, selected_ce
from .plan import load_plan


def append(path, value):
    with Path(path).open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, allow_nan=False) + "\n")


def save(path, value):
    path = Path(path)
    temp = path.with_suffix(".writing")
    torch.save(value, temp)
    os.replace(temp, path)


@lru_cache(maxsize=8)
def order(size, seed, stage, epoch):
    rows = list(range(size))
    random.Random(seed + 10_000 * stage + epoch).shuffle(rows)
    return rows


def optimizer_for(model, config):
    # Tied lexical weights occur once in named_parameters, and decay once.
    groups = [
        {
            "params": [p for p in model.parameters() if p.ndim >= 2],
            "weight_decay": config["weight_decay"],
        },
        {"params": [p for p in model.parameters() if p.ndim < 2], "weight_decay": 0.0},
    ]
    return torch.optim.AdamW(
        groups, lr=config["stages"][0]["learning_rate"], foreach=False
    )


def rate(stage, targets):
    if targets < stage["warmup_targets"]:
        return stage["learning_rate"] * (targets + 1) / stage["warmup_targets"]
    progress = (targets - stage["warmup_targets"]) / (
        stage["targets"] - stage["warmup_targets"]
    )
    return stage["minimum_lr"] + 0.5 * (
        stage["learning_rate"] - stage["minimum_lr"]
    ) * (1 + math.cos(math.pi * progress))


@torch.inference_mode()
def validate(model, data, config, device):
    model.eval()
    total, count = 0.0, 0
    for i in range(0, len(data), config["batch_size"]):
        rows = [data[j] for j in range(i, min(i + config["batch_size"], len(data)))]
        batch = make_batch(
            rows, pad_id=config["pad_id"], context=config["context"], device=device
        )
        loss, n = selected_ce(model, batch)
        total += float(loss) * n
        count += n
    model.train()
    return {
        "ce": total / count,
        "perplexity": math.exp(min(total / count, 80)),
        "targets": count,
        "perplexity_clipped": total / count > 80,
    }


def reconcile_log(path, committed_update):
    if not path.exists():
        return
    rows = read_rows(path)
    retained = [r for r in rows if r["update"] <= committed_update]
    discarded = [r for r in rows if r["update"] > committed_update]
    if discarded:
        for row in discarded:
            append(path.with_name("replayed-" + path.name), row)
        temporary = path.with_suffix(".writing")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            for row in retained:
                handle.write(json.dumps(row) + "\n")
        os.replace(temporary, path)


def execute(
    plan_path,
    run_id,
    root,
    *,
    seconds_limit,
    device="cpu",
    resume=False,
    max_updates=None,
):
    require_training_permission("model", run_id)
    if seconds_limit <= 0:
        raise ValueError("Positive soft wall cap required")
    plan = load_plan(plan_path)
    require_training_permission("model", run_id, plan_id=plan["plan_id"])
    run = next(r for r in plan["runs"] if r["id"] == run_id)
    config = plan["config"]
    torch.manual_seed(run["seed"])
    if device.startswith("cuda"):
        if not torch.cuda.is_available():
            raise ValueError("CUDA required, unavailable")
        torch.cuda.manual_seed_all(run["seed"])
        torch.cuda.reset_peak_memory_stats()
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    model = build_foundation(
        FoundationConfig(**plan["models"][run["kind"]]["config"]), seed=run["seed"]
    ).to(device)
    optimizer = optimizer_for(model, config)
    out = Path(root) / run_id
    out.mkdir(parents=True, exist_ok=True)
    if not resume and any(out.iterdir()):
        raise FileExistsError(out)
    identity = {
        "plan_id": plan["plan_id"],
        "run": run,
        "precision": "float32",
        "device_type": torch.device(device).type,
    }
    stats = {
        "stage": 0,
        "stage_targets": 0,
        "targets": 0,
        "input_tokens": 0,
        "updates": 0,
        "epoch": 0,
        "cursor": 0,
        "train_seconds": 0.0,
        "validation_seconds": 0.0,
    }
    if resume:
        saved = torch.load(out / "latest.pt", map_location="cpu", weights_only=True)
        if saved["identity"] != identity:
            raise ValueError("Checkpoint identity differs")
        model.load_state_dict(saved["model"])
        optimizer.load_state_dict(saved["optimizer"])
        torch.set_rng_state(saved["rng_cpu"])
        if device.startswith("cuda"):
            torch.cuda.set_rng_state_all(saved["rng_cuda"])
        stats = saved["stats"]
        reconcile_log(out / "metrics.jsonl", stats["updates"])
        reconcile_log(out / "validation.jsonl", stats["updates"])
    start = time.perf_counter()
    initial_updates = stats["updates"]
    initial_train = stats["train_seconds"]
    append(
        out / "environment.jsonl",
        {
            "utc": datetime.now(UTC).isoformat(),
            "resume": resume,
            "torch": str(torch.__version__),
            "python": platform.python_version(),
            "device": device,
            "gpu": torch.cuda.get_device_name() if device.startswith("cuda") else None,
            "soft_seconds": seconds_limit,
        },
    )

    def checkpoint(name="latest.pt"):
        value = {
            "identity": identity,
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "stats": dict(stats),
            "rng_cpu": torch.get_rng_state(),
            "rng_cuda": torch.cuda.get_rng_state_all()
            if device.startswith("cuda")
            else None,
            "complete": stats["stage"] == len(config["stages"]),
        }
        save(out / name, value)

    data = None
    while stats["stage"] < len(config["stages"]):
        stage_index = stats["stage"]
        stage = config["stages"][stage_index]
        if data is None:
            data = TokenDataset(plan["data_dir"], "train", stage["name"])
        if stats["stage_targets"] == stage["targets"]:
            # Validation is never a completion prerequisite that could lose exposure.
            before = time.perf_counter()
            valid = validate(
                model,
                TokenDataset(plan["data_dir"], "validation", stage["name"]),
                config,
                device,
            )
            elapsed = time.perf_counter() - before
            stats["validation_seconds"] += elapsed
            append(
                out / "validation.jsonl",
                {
                    "update": stats["updates"],
                    "stage": stage["name"],
                    "trained_targets": stats["targets"],
                    **valid,
                    "seconds": elapsed,
                },
            )
            checkpoint(stage["name"] + "-final.pt")
            stats.update(stage=stage_index + 1, stage_targets=0, epoch=0, cursor=0)
            if stats["stage"] < len(config["stages"]):
                optimizer = optimizer_for(
                    model, config
                )  # Explicit fresh moments for SFT.
            data = None
            checkpoint()
            continue
        if time.perf_counter() - start >= seconds_limit or (
            max_updates is not None
            and stats["updates"] - initial_updates >= max_updates
        ):
            break
        rows = []
        cursor, epoch = stats["cursor"], stats["epoch"]
        remaining = stage["targets"] - stats["stage_targets"]
        available = remaining
        while len(rows) < config["batch_size"] and available > 0:
            row = data[order(len(data), run["seed"], stage_index, epoch)[cursor]]
            rows.append(row)
            available -= sum(t != -100 for t in row["targets"])
            cursor += 1
            if cursor == len(data):
                cursor, epoch = 0, epoch + 1
        batch = make_batch(
            rows,
            pad_id=config["pad_id"],
            context=config["context"],
            remaining=remaining,
            device=device,
        )
        model.train()
        lr = rate(stage, stats["stage_targets"])
        for group in optimizer.param_groups:
            group["lr"] = lr
        if device.startswith("cuda"):
            torch.cuda.synchronize()
        before = time.perf_counter()
        optimizer.zero_grad(set_to_none=True)
        loss, count = selected_ce(model, batch)
        if not torch.isfinite(loss):
            raise FloatingPointError("Nonfinite objective")
        loss.backward()
        norm = torch.nn.utils.clip_grad_norm_(
            model.parameters(), config["grad_clip"], error_if_nonfinite=True
        )
        optimizer.step()
        if device.startswith("cuda"):
            torch.cuda.synchronize()
        elapsed = time.perf_counter() - before
        stats.update(
            stage_targets=stats["stage_targets"] + count,
            targets=stats["targets"] + count,
            input_tokens=stats["input_tokens"] + int(batch["attention_mask"].sum()),
            updates=stats["updates"] + 1,
            cursor=cursor,
            epoch=epoch,
            train_seconds=stats["train_seconds"] + elapsed,
        )
        append(
            out / "metrics.jsonl",
            {
                "update": stats["updates"],
                "stage": stage["name"],
                "targets": stats["targets"],
                "stage_targets": stats["stage_targets"],
                "batch_targets": count,
                "input_tokens": int(batch["attention_mask"].sum()),
                "ce": float(loss.detach()),
                "grad_norm_before_clip": float(norm),
                "learning_rate": lr,
                "train_seconds": elapsed,
                "epoch": epoch,
                "cursor": cursor,
            },
        )
        if stats["updates"] % config["checkpoint_every_updates"] == 0:
            checkpoint()
    checkpoint()
    if stats["stage"] == len(config["stages"]):
        checkpoint("final.pt")
    return {
        "run": run_id,
        "complete": stats["stage"] == len(config["stages"]),
        "stats": stats,
        "checkpoint_sha256": sha256(out / "latest.pt"),
        "invocation_seconds": time.perf_counter() - start,
        "invocation_train_seconds": stats["train_seconds"] - initial_train,
        "peak_allocated_bytes": torch.cuda.max_memory_allocated()
        if device.startswith("cuda")
        else None,
    }
