"""Training implementation. The permission gate is checked before any work.

This module is prepared but optimizer/resume integration is deliberately not
executed while the user has training on hold.
"""

from __future__ import annotations

import json
import math
import os
import platform
import random
import sys
import time
from dataclasses import asdict
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

import torch

from ..models import ModelConfig, build_model, parameter_count
from ..tokenizer import ByteTokenizer
from ..training_gate import require_training_permission
from .data import arm_examples
from .io import read_rows, sha256, write_json
from .objectives import batch_examples, ce_loss, probe_js
from .plan import load_plan


def language_examples(rows, split, context):
    examples = []
    t = ByteTokenizer()
    for row in rows:
        if row["split"] != split:
            continue
        ids = t.encode(row["text"], bos=True, eos=True)
        for start in range(0, len(ids) - 1, context):
            chunk = ids[start : start + context + 1]
            examples.append(
                {
                    "source_id": row["source_id"],
                    "input_ids": chunk[:-1],
                    "targets": chunk[1:],
                }
            )
    if not examples:
        raise ValueError(f"No language examples for {split}")
    return examples


@lru_cache(maxsize=16)
def shuffled_order(size, seed, epoch):
    order = list(range(size))
    random.Random(seed + epoch).shuffle(order)
    return tuple(order)


def take_batch(examples, seed, epoch, cursor, size):
    result = []
    while len(result) < size:
        order = shuffled_order(len(examples), seed, epoch)
        available = min(size - len(result), len(order) - cursor)
        result.extend(examples[i] for i in order[cursor : cursor + available])
        cursor += available
        if cursor == len(order):
            epoch += 1
            cursor = 0
    return result, epoch, cursor


@torch.no_grad()
def validation_loss(model, examples, context, batch_size, device):
    was_training = model.training
    model.eval()
    total = 0.0
    tokens = 0
    for start in range(0, len(examples), batch_size):
        loss, n = ce_loss(
            model, batch_examples(examples[start : start + batch_size], context, device)
        )
        total += float(loss) * n
        tokens += n
    model.train(was_training)
    return {
        "ce": total / tokens,
        "perplexity": math.exp(min(total / tokens, 80)),
        "targets": tokens,
        "perplexity_clipped": total / tokens > 80,
    }


def atomic_checkpoint(path, value):
    path = Path(path)
    tmp = path.with_suffix(".tmp")
    torch.save(value, tmp)
    os.replace(tmp, path)


def restore_checkpoint(path, model, optimizer, *, expected):
    value = torch.load(path, map_location="cpu", weights_only=True)
    if value["identity"] != expected:
        raise ValueError("Checkpoint identity/config/input mismatch")
    model.load_state_dict(value["model"])
    optimizer.load_state_dict(value["optimizer"])
    torch.set_rng_state(value["rng_cpu"])
    if torch.cuda.is_available() and value["rng_cuda"] is not None:
        torch.cuda.set_rng_state_all(value["rng_cuda"])
    return value


def execute(
    plan_path, run_id, output_root, *, seconds_limit, device="cpu", resume=False
):
    require_training_permission("model", run_id)
    if seconds_limit <= 0:
        raise ValueError("Explicit positive time limit required")
    plan = load_plan(plan_path)
    require_training_permission("model", run_id, plan_id=plan["plan_id"])
    c = plan["config"]
    run = next((r for r in plan["runs"] if r["id"] == run_id), None)
    if run is None:
        raise ValueError("Unknown run ID")
    if device.startswith("cuda") and not torch.cuda.is_available():
        raise ValueError("CUDA unavailable")
    torch.manual_seed(run["seed"])
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(run["seed"])
    model_config = ModelConfig(**plan["models"][run["kind"]]["config"])
    model = build_model(model_config).to(device)
    out = Path(output_root) / run_id
    out.mkdir(parents=True, exist_ok=True)
    if not resume and any(out.iterdir()):
        raise FileExistsError(out)
    bundles = read_rows(Path(plan["data_dir"]) / "train.jsonl")
    by_source = {b["source_id"]: b for b in bundles}
    if run["phase"] == "warmup":
        warm = read_rows(plan["warmup"])
        examples = language_examples(warm, "train", c["context"])
        valid = language_examples(warm, "validation", c["context"])
    else:
        examples = arm_examples(bundles, run["arm"])
        valid = arm_examples(
            read_rows(Path(plan["data_dir"]) / "validation.jsonl"), "A1"
        )
    parent_sha = None
    if run["parent"]:
        path = Path(output_root) / run["parent"] / "final.pt"
        parent = torch.load(path, map_location="cpu", weights_only=True)
        if (
            parent["plan_id"] != plan["plan_id"]
            or not parent["complete"]
            or parent["run"]["id"] != run["parent"]
        ):
            raise ValueError("Parent warm-up is incomplete or from another plan")
        model.load_state_dict(parent["model"])
        parent_sha = sha256(path)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=c["learning_rate"], weight_decay=c["weight_decay"]
    )
    identity = {
        "plan_id": plan["plan_id"],
        "run": run,
        "model_config": asdict(model_config),
        "parent_sha256": parent_sha,
        "device_type": torch.device(device).type,
        "batch_size": c["batch_size"],
        "precision": "float32",
    }
    stats = {
        "trained_targets": 0,
        "processed_input_tokens": 0,
        "probe_input_tokens": 0,
        "probe_positions": 0,
        "updates": 0,
        "epoch": 0,
        "cursor": 0,
        "train_seconds": 0.0,
        "validation_seconds": 0.0,
        "best_validation_ce": None,
    }
    if resume:
        saved = restore_checkpoint(
            out / "latest.pt", model, optimizer, expected=identity
        )
        stats = saved["stats"]
        if (out / "metrics.jsonl").exists():
            events = read_rows(out / "metrics.jsonl")
            discarded = [e for e in events if e["update"] > stats["updates"]]
            if discarded:
                with (out / "metrics.jsonl").open("w", encoding="utf-8") as handle:
                    for e in events:
                        if e["update"] <= stats["updates"]:
                            handle.write(json.dumps(e) + "\n")
                with (out / "replayed-work.jsonl").open(
                    "a", encoding="utf-8"
                ) as handle:
                    for e in discarded:
                        handle.write(json.dumps(e) + "\n")
        if (out / "validation.jsonl").exists():
            records = read_rows(out / "validation.jsonl")
            discarded_validation = [
                e for e in records if e["update"] > stats["updates"]
            ]
            if discarded_validation:
                with (out / "validation.jsonl").open("w", encoding="utf-8") as handle:
                    for e in records:
                        if e["update"] <= stats["updates"]:
                            handle.write(json.dumps(e) + "\n")
                with (out / "replayed-validation-work.jsonl").open(
                    "a", encoding="utf-8"
                ) as handle:
                    for e in discarded_validation:
                        handle.write(json.dumps(e) + "\n")
    elif (out / "latest.pt").exists():
        raise FileExistsError(out / "latest.pt")
    if device.startswith("cuda"):
        torch.cuda.reset_peak_memory_stats()
    start = time.perf_counter()
    invocation_train = 0.0
    invocation_validation = 0.0
    invocation_started_utc = datetime.now(UTC).isoformat()
    with (out / "environment.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "started_utc": invocation_started_utc,
                    "resume": resume,
                    "python": sys.version,
                    "platform": platform.platform(),
                    "torch": torch.__version__,
                    "cuda": torch.version.cuda,
                    "cudnn": torch.backends.cudnn.version(),
                    "gpu": torch.cuda.get_device_name()
                    if device.startswith("cuda")
                    else None,
                    "gpu_total_bytes": torch.cuda.get_device_properties(0).total_memory
                    if device.startswith("cuda")
                    else None,
                    "precision": "float32",
                    "plan_id": plan["plan_id"],
                    "actual_parameters": parameter_count(model),
                    "config": c,
                    "dataset_id": plan["dataset_id"],
                    "warmup_sha256": plan["warmup_sha256"],
                    "parent_sha256": parent_sha,
                }
            )
            + "\n"
        )

    def checkpoint(complete=False):
        return {
            "schema_version": 1,
            "identity": identity,
            "plan_id": plan["plan_id"],
            "run": run,
            "config": asdict(model_config),
            "tokenizer_sha256": None,
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "stats": dict(stats),
            "complete": complete,
            "rng_cpu": torch.get_rng_state(),
            "rng_cuda": torch.cuda.get_rng_state_all()
            if torch.cuda.is_available()
            else None,
        }

    # Initial state checkpoint makes a zero-update interrupted run resumable.
    if not resume:
        atomic_checkpoint(out / "latest.pt", checkpoint())
    try:
        while (
            stats["trained_targets"] < run["targets"]
            and time.perf_counter() - start < seconds_limit
        ):
            tic = time.perf_counter()
            model.train()
            items, epoch, cursor = take_batch(
                examples, run["seed"], stats["epoch"], stats["cursor"], c["batch_size"]
            )
            batch = batch_examples(
                items,
                c["context"],
                device,
                remaining=run["targets"] - stats["trained_targets"],
            )
            optimizer.zero_grad(set_to_none=True)
            loss, n = ce_loss(model, batch)
            extra = {"probe_input_tokens": 0, "probe_positions": 0}
            js = loss.new_zeros(())
            if run.get("arm") == "A3":
                key = ("holder", "action", "cabinet", "power_available", "permission")[
                    stats["updates"] % 5
                ]
                js, extra = probe_js(
                    model,
                    by_source[items[0]["source_id"]],
                    c["context"],
                    device,
                    probe_key=key,
                )
            objective = loss + c["js_weight"] * js
            if not torch.isfinite(objective):
                raise FloatingPointError("Non-finite loss")
            objective.backward()
            norm = torch.nn.utils.clip_grad_norm_(
                model.parameters(), c["grad_clip"], error_if_nonfinite=True
            )
            optimizer.step()
            if device.startswith("cuda"):
                torch.cuda.synchronize()
            elapsed = time.perf_counter() - tic
            invocation_train += elapsed
            stats.update(epoch=epoch, cursor=cursor)
            stats["trained_targets"] += n
            stats["processed_input_tokens"] += int(batch["attention_mask"].sum())
            for k, v in extra.items():
                stats[k] += v
            stats["updates"] += 1
            stats["train_seconds"] += elapsed
            event = {
                "utc": datetime.now(UTC).isoformat(),
                "update": stats["updates"],
                "targets": stats["trained_targets"],
                "ce": float(loss.detach()),
                "js": float(js.detach()),
                "gradient_norm": float(norm),
                "seconds": elapsed,
                "objective": float(objective.detach()),
                "target_delta": n,
                "processed_input_tokens": stats["processed_input_tokens"],
                "batch_input_tokens": int(batch["attention_mask"].sum()),
                "learning_rate": optimizer.param_groups[0]["lr"],
                "supervised_targets_per_train_second": n / elapsed,
                "probe_input_tokens": extra["probe_input_tokens"],
                "probe_positions": extra["probe_positions"],
                "epoch": epoch,
                "cursor": cursor,
                "peak_allocated_bytes": torch.cuda.max_memory_allocated()
                if device.startswith("cuda")
                else None,
                "peak_reserved_bytes": torch.cuda.max_memory_reserved()
                if device.startswith("cuda")
                else None,
            }
            with (out / "metrics.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
            if (
                stats["updates"]
                % c.get("validation_every_updates", c["checkpoint_every_updates"])
                == 0
                or stats["trained_targets"] == run["targets"]
            ):
                tic = time.perf_counter()
                v = validation_loss(model, valid, c["context"], c["batch_size"], device)
                if device.startswith("cuda"):
                    torch.cuda.synchronize()
                dt = time.perf_counter() - tic
                invocation_validation += dt
                stats["validation_seconds"] += dt
                improved = (
                    stats["best_validation_ce"] is None
                    or v["ce"] < stats["best_validation_ce"]
                )
                if improved:
                    stats["best_validation_ce"] = v["ce"]
                with (out / "validation.jsonl").open("a", encoding="utf-8") as f:
                    f.write(
                        json.dumps(
                            {
                                "utc": datetime.now(UTC).isoformat(),
                                "update": stats["updates"],
                                "trained_targets": stats["trained_targets"],
                                "seconds": dt,
                                "corpus": "mixed warmup validation"
                                if run["phase"] == "warmup"
                                else "controlled A1 validation",
                                **v,
                            }
                        )
                        + "\n"
                    )
                saved = checkpoint()
                atomic_checkpoint(out / "latest.pt", saved)
                if improved:
                    atomic_checkpoint(out / "best.pt", saved)
            elif stats["updates"] % c["checkpoint_every_updates"] == 0:
                atomic_checkpoint(out / "latest.pt", checkpoint())
        complete = stats["trained_targets"] == run["targets"]
        saved = checkpoint(complete)
        atomic_checkpoint(out / "latest.pt", saved)
        if complete:
            atomic_checkpoint(out / "final.pt", saved)
    except BaseException:
        # Do not serialize possibly half-completed optimizer updates. Resume the
        # last complete atomic checkpoint; uncheckpointed work must be accounted.
        write_json(
            out / "interruption.json",
            {
                "last_checkpoint_sha256": sha256(out / "latest.pt"),
                "uncheckpointed_updates_may_be_replayed": True,
                "elapsed_invocation": time.perf_counter() - start,
            },
            replace=True,
        )
        raise
    report = {
        "plan_id": plan["plan_id"],
        "invocation_started_utc": invocation_started_utc,
        "invocation_finished_utc": datetime.now(UTC).isoformat(),
        "config": c,
        "dataset_id": plan["dataset_id"],
        "checkpoint_sha256": sha256(out / "latest.pt"),
        "run": run,
        "actual_parameters": parameter_count(model),
        "stats": stats,
        "complete": complete,
        "parent_sha256": parent_sha,
        "precision": "float32",
        "device": str(device),
        "cuda_name": torch.cuda.get_device_name()
        if device.startswith("cuda")
        else None,
        "peak_allocated_bytes": torch.cuda.max_memory_allocated()
        if device.startswith("cuda")
        else None,
        "peak_reserved_bytes": torch.cuda.max_memory_reserved()
        if device.startswith("cuda")
        else None,
        "forward_backward_flop_proxy": 6
        * parameter_count(model)
        * stats["processed_input_tokens"],
        "flop_proxy_excludes": "attention quadratic term, JS probe passes, validation, generation and optimizer",
        "invocation_seconds": time.perf_counter() - start,
        "invocation_train_seconds": invocation_train,
        "invocation_validation_seconds": invocation_validation,
    }
    write_json(out / "run.json", report, replace=True)
    return report
