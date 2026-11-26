"""Readiness checks with zero optimizer steps and unchanged parameters."""

from __future__ import annotations

import platform
import sys
import time
from pathlib import Path

import torch

from ..models import ModelConfig, build_model, parameter_count
from ..training_gate import POLICY
from .data import arm_examples
from .io import read_json, read_rows, sha256, write_json
from .objectives import batch_examples, ce_loss, probe_js
from .plan import load_plan


def preflight(plan_path, output, *, device="cpu"):
    plan = load_plan(plan_path)
    if read_json(POLICY).get("tokenizer_fitting_authorized") is not False:
        raise ValueError("The fixed-byte pipeline does not authorize tokenizer fitting")
    torch.set_num_threads(2)
    reports = []
    bundles = read_rows(Path(plan["data_dir"]) / "train.jsonl")
    context = plan["config"]["context"]
    for kind, item in plan["models"].items():
        torch.manual_seed(123)
        if device.startswith("cuda"):
            torch.cuda.reset_peak_memory_stats()
        model = build_model(ModelConfig(**item["config"])).to(device).eval()
        before = {k: v.detach().clone() for k, v in model.state_dict().items()}
        batch = batch_examples(
            arm_examples(bundles[:1], "A1")[: plan["config"]["batch_size"]],
            context,
            device,
        )
        tic = time.perf_counter()
        loss, n = ce_loss(model, batch)
        loss.backward()
        if not torch.isfinite(loss) or not all(
            p.grad is not None and torch.isfinite(p.grad).all()
            for p in model.parameters()
        ):
            raise FloatingPointError("Invalid CE gradients")
        model.zero_grad(set_to_none=True)
        js, extra = probe_js(model, bundles[0], context, device, probe_key="action")
        js.backward()
        if not torch.isfinite(js):
            raise FloatingPointError("Invalid JS loss")
        if not all(torch.equal(v, before[k]) for k, v in model.state_dict().items()):
            raise AssertionError("Parameters changed")
        ids = batch["input_ids"][:, :17]
        with torch.no_grad():
            full, _ = model(ids)
            changed = ids.clone()
            changed[:, -1] = (changed[:, -1] + 1) % 259
            other, _ = model(changed)
            torch.testing.assert_close(
                full[:, :-1], other[:, :-1], rtol=1e-5, atol=1e-6
            )
            state = None
            parts = []
            for i in range(ids.shape[1]):
                logits, _, state = model(
                    ids[:, i : i + 1], state=state, return_state=True
                )
                parts.append(logits)
            torch.testing.assert_close(full, torch.cat(parts, 1), rtol=2e-5, atol=2e-6)
            reset, _ = model(ids)
            torch.testing.assert_close(full, reset, rtol=0, atol=0)
        reports.append(
            {
                "kind": kind,
                "actual_parameters": parameter_count(model),
                "ce_targets": n,
                "input_tokens": int(batch["attention_mask"].sum()),
                "probe_accounting": extra,
                "forward_backward_checks_seconds": time.perf_counter() - tic,
                "parameters_unchanged": True,
                "causal_step_reset_checks": True,
                "optimizer_steps": 0,
                "batch_size_checked": int(batch["input_ids"].shape[0]),
                "peak_allocated_bytes": torch.cuda.max_memory_allocated()
                if device.startswith("cuda")
                else None,
                "peak_reserved_bytes": torch.cuda.max_memory_reserved()
                if device.startswith("cuda")
                else None,
            }
        )
    result = {
        "plan_id": plan["plan_id"],
        "plan_sha256": sha256(plan_path),
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "device": device,
        "cuda_available": torch.cuda.is_available(),
        "gpu_name": torch.cuda.get_device_name() if torch.cuda.is_available() else None,
        "models": reports,
        "training_authorized": False,
        "tokenizer_fitted": False,
        "train_throughput": None,
        "colab_gpu_and_cu_rate": None,
        "status": "non_optimizing_checks_passed; optimizer integration/overfit/resume awaits authorization",
        "scientific_gates_pending": [
            "naturalistic licensed transfer set",
            "real blinded labels",
            "GPU-hour/CU budget calibration",
            "smallest useful effect and preregistration",
        ],
    }
    write_json(output, result)
    return result


def compute_budget(plan_path, measurement=None):
    plan = load_plan(plan_path)
    if measurement is None:
        return {
            "budget": plan["budget"],
            "gpu_hours": None,
            "cost_usd": None,
            "reason": "No actual training/CU measurement; purchased $50 plan is user-reported, exact SKU and available credits unverified.",
        }
    observed = read_json(measurement)
    predicted = []
    for run in plan["runs"]:
        category = "warmup" if run["phase"] == "warmup" else run["arm"]
        key = f"{run['kind']}/{category}"
        m = observed[key]
        if min(m["targets"], m["seconds"], m["cu_spent"]) <= 0:
            raise ValueError("Positive observed counters required")
        hours = run["targets"] / m["targets"] * m["seconds"] / 3600
        predicted.append(
            {
                "run_id": run["id"],
                "estimated_hours": hours,
                "estimated_cu": run["targets"] / m["targets"] * m["cu_spent"],
            }
        )
    return {
        "estimates": predicted,
        "gpu_hours": sum(r["estimated_hours"] for r in predicted),
        "cu": sum(r["estimated_cu"] for r in predicted),
        "excludes": "selection reserve, validation/generation/idle unless included in observations",
        "assumption": "Same GPU/runtime and workload as each observation; no fixed CU/hour assumption",
    }
