"""Budget-exact subword post training; permission and writing gate fail closed.

The foundation implementation remains immutable. Primary post plans/run IDs
are not authorized by preparing this module or by passing synthetic tests.
"""

import math
import platform
import time
from datetime import UTC, datetime
from pathlib import Path

import torch

from ..foundation.codec import FrozenTokenizer
from ..foundation.modeling import FoundationConfig, build_foundation
from ..foundation.plan import load_plan as load_foundation_plan
from ..foundation.runner import append, reconcile_log, save
from ..q3a.data import arm_examples
from ..q3a.io import read_rows, sha256, write_json
from ..q3a.runner import take_batch
from ..training_gate import require_training_permission
from .foundation_review import check_complete_parent
from .objectives import batch_examples, ce_loss, probe_js
from .plan import load_plan


@torch.inference_mode()
def validation_loss(model, rows, tokenizer, config, device):
    was_training = model.training
    model.eval()
    total, count = 0.0, 0
    try:
        for i in range(0, len(rows), config["batch_size"]):
            batch = batch_examples(
                rows[i : i + config["batch_size"]], tokenizer, config["context"], device
            )
            loss, n = ce_loss(model, batch)
            total += float(loss) * n
            count += n
    finally:
        model.train(was_training)
    if not count or not math.isfinite(total):
        raise ValueError("Empty or nonfinite validation")
    return {
        "ce": total / count,
        "targets": count,
        "perplexity": math.exp(min(total / count, 80)),
        "perplexity_clipped": total / count > 80,
        "corpus": "controlled A1 validation, response-only BPE targets",
    }


def execute(
    plan_path,
    run_id,
    output_root,
    *,
    seconds_limit,
    device="cpu",
    resume=False,
    max_updates=None,
):
    require_training_permission("model", run_id)
    if not math.isfinite(seconds_limit) or seconds_limit <= 0:
        raise ValueError("Explicit finite positive wall cap required")
    if max_updates is not None and (type(max_updates) is not int or max_updates < 0):
        raise ValueError("Invalid engineering update cap")
    plan = load_plan(plan_path)
    require_training_permission("model", run_id, plan_id=plan["plan_id"])
    if plan["writing_gate"] is None:
        raise ValueError(
            "Writing feasibility has not been reviewed; post training held"
        )
    config = plan["config"]
    if config.get("gpu_hours_cap_per_study") is None:
        raise ValueError("A measured finite study budget is still required")
    run = next((r for r in plan["runs"] if r["id"] == run_id), None)
    if run is None:
        raise ValueError("Unknown subword post run")
    # Match the reviewed explicit inference path in diagnostic validation.
    # Real post runs remain held; this does not modify the active foundation.
    torch.backends.mha.set_fastpath_enabled(False)
    if device.startswith("cuda"):
        if not torch.cuda.is_available():
            raise ValueError("CUDA unavailable")
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.cuda.manual_seed_all(run["seed"])
        torch.cuda.reset_peak_memory_stats()
    torch.manual_seed(run["seed"])
    parent = plan["parents"][run["parent_key"]]
    if parent["run"]["seed"] != run["seed"] or parent["run"]["kind"] != run["kind"]:
        raise ValueError("Post seed must use its own foundation seed")
    foundation = load_foundation_plan(parent["foundation_plan"])
    saved_parent = torch.load(
        parent["checkpoint"], map_location="cpu", weights_only=True
    )
    check_complete_parent(saved_parent, foundation, parent["run"])
    model = build_foundation(
        FoundationConfig(**plan["models"][run["kind"]]["config"]), seed=run["seed"]
    ).to(device)
    model.load_state_dict(saved_parent["model"], strict=True)
    del saved_parent
    if (
        sum(p.numel() for p in model.parameters())
        != plan["models"][run["kind"]]["actual_parameters"]
    ):
        raise ValueError("Actual parameter count differs")
    optimizer = torch.optim.AdamW(
        [
            {
                "params": [p for p in model.parameters() if p.ndim >= 2],
                "weight_decay": config["weight_decay"],
            },
            {
                "params": [p for p in model.parameters() if p.ndim < 2],
                "weight_decay": 0.0,
            },
        ],
        lr=config["learning_rate"],
        foreach=False,
    )
    tokenizer = FrozenTokenizer(plan["tokenizer"], plan["tokenizer_spec"])
    bundles = read_rows(Path(plan["data_dir"]) / "train.jsonl")
    by_source = {b["source_id"]: b for b in bundles}
    rows = arm_examples(bundles, run["arm"])
    valid = arm_examples(read_rows(Path(plan["data_dir"]) / "validation.jsonl"), "A1")
    out = Path(output_root) / run_id
    out.mkdir(parents=True, exist_ok=True)
    if not resume and any(out.iterdir()):
        raise FileExistsError(out)
    identity = {
        "plan_id": plan["plan_id"],
        "run": run,
        "parent_sha256": parent["checkpoint_sha256"],
        "precision": "float32_TF32_disabled",
        "mha_fastpath_enabled": False,
        "device_type": torch.device(device).type,
    }
    stats = {
        "targets": 0,
        "input_tokens": 0,
        "probe_input_tokens": 0,
        "probe_positions": 0,
        "updates": 0,
        "epoch": 0,
        "cursor": 0,
        "update_wall_seconds": 0.0,
        "validation_seconds": 0.0,
    }
    if resume:
        previous = torch.load(out / "latest.pt", map_location="cpu", weights_only=True)
        if previous["identity"] != identity:
            raise ValueError("Post resume identity differs")
        model.load_state_dict(previous["model"], strict=True)
        optimizer.load_state_dict(previous["optimizer"])
        torch.set_rng_state(previous["rng_cpu"])
        if device.startswith("cuda"):
            torch.cuda.set_rng_state_all(previous["rng_cuda"])
        stats = previous["stats"]
        reconcile_log(out / "metrics.jsonl", stats["updates"])
        reconcile_log(out / "validation.jsonl", stats["updates"])
        del previous
    append(
        out / "environment.jsonl",
        {
            "utc": datetime.now(UTC).isoformat(),
            "resume": resume,
            "torch": str(torch.__version__),
            "python": platform.python_version(),
            "device": device,
            "gpu": torch.cuda.get_device_name() if device.startswith("cuda") else None,
            "soft_seconds_limit": seconds_limit,
            "mha_fastpath_enabled": torch.backends.mha.get_fastpath_enabled(),
        },
    )

    def checkpoint(name="latest.pt"):
        save(
            out / name,
            {
                "identity": identity,
                "plan_id": plan["plan_id"],
                "run": run,
                "config": plan["models"][run["kind"]]["config"],
                "tokenizer_spec": plan["tokenizer_spec"],
                "parent_sha256": parent["checkpoint_sha256"],
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "stats": dict(stats),
                "complete": stats["targets"] == run["targets"],
                "rng_cpu": torch.get_rng_state(),
                "rng_cuda": torch.cuda.get_rng_state_all()
                if device.startswith("cuda")
                else None,
            },
        )

    if not resume:
        checkpoint()  # Safe rollback exists before any optimizer update.
    started, initial_updates = time.perf_counter(), stats["updates"]
    try:
        while (
            stats["targets"] < run["targets"]
            and time.perf_counter() - started < seconds_limit
        ):
            if (
                max_updates is not None
                and stats["updates"] - initial_updates >= max_updates
            ):
                break
            model.train()
            if device.startswith("cuda"):
                torch.cuda.synchronize()
            tic = time.perf_counter()
            items, epoch, cursor = take_batch(
                rows, run["seed"], stats["epoch"], stats["cursor"], config["batch_size"]
            )
            batch = batch_examples(
                items,
                tokenizer,
                config["context"],
                device,
                remaining=run["targets"] - stats["targets"],
            )
            optimizer.zero_grad(set_to_none=True)
            ce, targets = ce_loss(model, batch)
            js = ce.new_zeros(())
            extra = {"probe_input_tokens": 0, "probe_positions": 0}
            if run["arm"] == "A3":
                key = ("holder", "action", "cabinet", "power_available", "permission")[
                    stats["updates"] % 5
                ]
                js, extra = probe_js(
                    model,
                    tokenizer,
                    by_source[items[0]["source_id"]],
                    config["context"],
                    device,
                    key,
                )
            loss = ce + config["js_weight"] * js
            if not torch.isfinite(loss):
                raise FloatingPointError("Nonfinite subword post objective")
            loss.backward()
            norm = torch.nn.utils.clip_grad_norm_(
                model.parameters(), config["grad_clip"], error_if_nonfinite=True
            )
            optimizer.step()
            if device.startswith("cuda"):
                torch.cuda.synchronize()
            elapsed = time.perf_counter() - tic
            stats.update(
                targets=stats["targets"] + targets,
                input_tokens=stats["input_tokens"] + int(batch["attention_mask"].sum()),
                updates=stats["updates"] + 1,
                epoch=epoch,
                cursor=cursor,
                update_wall_seconds=stats["update_wall_seconds"] + elapsed,
                probe_input_tokens=stats["probe_input_tokens"]
                + extra["probe_input_tokens"],
                probe_positions=stats["probe_positions"] + extra["probe_positions"],
            )
            append(
                out / "metrics.jsonl",
                {
                    "utc": datetime.now(UTC).isoformat(),
                    "update": stats["updates"],
                    "targets": stats["targets"],
                    "batch_targets": targets,
                    "ce": float(ce.detach()),
                    "js": float(js.detach()),
                    "objective": float(loss.detach()),
                    "grad_norm_before_clip": float(norm),
                    "learning_rate": config["learning_rate"],
                    "input_tokens": int(batch["attention_mask"].sum()),
                    **extra,
                    "update_wall_seconds": elapsed,
                    "epoch": epoch,
                    "cursor": cursor,
                    "peak_allocated_bytes": torch.cuda.max_memory_allocated()
                    if device.startswith("cuda")
                    else None,
                },
            )
            if (
                stats["updates"] % config["validation_every_updates"] == 0
                or stats["targets"] == run["targets"]
            ):
                tic = time.perf_counter()
                value = validation_loss(model, valid, tokenizer, config, device)
                elapsed = time.perf_counter() - tic
                stats["validation_seconds"] += elapsed
                append(
                    out / "validation.jsonl",
                    {
                        "update": stats["updates"],
                        "targets_trained": stats["targets"],
                        "seconds": elapsed,
                        **value,
                    },
                )
                checkpoint()
            elif stats["updates"] % config["checkpoint_every_updates"] == 0:
                checkpoint()
    except BaseException:
        write_json(
            out / "interruption.json",
            {
                "last_committed_checkpoint_sha256": sha256(out / "latest.pt"),
                "uncheckpointed_work_may_be_replayed": True,
            },
            replace=True,
        )
        raise
    checkpoint()
    complete = stats["targets"] == run["targets"]
    if complete:
        checkpoint("final.pt")
    result = {
        "plan_id": plan["plan_id"],
        "run": run,
        "stats": stats,
        "complete": complete,
        "actual_parameters": sum(p.numel() for p in model.parameters()),
        "parent_sha256": parent["checkpoint_sha256"],
        "latest_sha256": sha256(out / "latest.pt"),
        "invocation_seconds": time.perf_counter() - started,
        "test_evaluated": False,
        "primary_output_is_natural_story": True,
        "inference_gold_state_table": False,
        "validation_selection": "diagnostic only; final exact-budget checkpoint required",
    }
    write_json(out / "run.json", result, replace=True)
    return result
