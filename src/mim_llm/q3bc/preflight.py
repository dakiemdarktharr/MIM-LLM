"""Non-optimizing contracts; C fixtures are explicitly not self-origin data."""

from __future__ import annotations

import torch

from ..models import ModelConfig, build_model, parameter_count
from ..q3a.io import read_json, write_json
from ..training_gate import POLICY
from .objectives import examples_for, loss_batch
from .plan import load_plan


def preflight(plan_path, output, *, device="cpu"):
    plan = load_plan(plan_path)
    torch.set_num_threads(2)
    permission = read_json(POLICY)
    if (
        permission["model_training_authorized"]
        or permission["tokenizer_fitting_authorized"]
    ):
        raise ValueError("Preparation requires closed permission")
    checks = []
    for kind in plan["config"]["backbones"]:
        model = (
            build_model(ModelConfig(**plan["models"][kind]["config"])).to(device).eval()
        )
        for arm in plan["config"]["arms"]:
            if device.startswith("cuda"):
                torch.cuda.reset_peak_memory_stats()
            run = next(r for r in plan["runs"] if r["kind"] == kind and r["arm"] == arm)
            items = examples_for(plan, run, contract_fixture=True)[
                : plan["config"]["batch_size"]
            ]
            before = {k: v.detach().clone() for k, v in model.state_dict().items()}
            model.zero_grad(set_to_none=True)
            loss, n, extra = loss_batch(
                model, items, plan, run, remaining=100000, device=device
            )
            loss.backward()
            if not torch.isfinite(loss) or not all(
                p.grad is not None and torch.isfinite(p.grad).all()
                for p in model.parameters()
            ):
                raise FloatingPointError("Invalid gradients")
            if not all(
                torch.equal(v, before[k]) for k, v in model.state_dict().items()
            ):
                raise ValueError("Parameters changed")
            checks.append(
                {
                    "kind": kind,
                    "arm": arm,
                    "actual_parameters": parameter_count(model),
                    "targets_checked": n,
                    "accounting": extra,
                    "optimizer_steps": 0,
                    "peak_allocated_bytes": torch.cuda.max_memory_allocated()
                    if device.startswith("cuda")
                    else None,
                    "peak_reserved_bytes": torch.cuda.max_memory_reserved()
                    if device.startswith("cuda")
                    else None,
                    "parameters_unchanged": True,
                }
            )
    result = {
        "plan_id": plan["plan_id"],
        "study": plan["study"],
        "device": device,
        "checks": checks,
        "optimizer_steps": 0,
        "C_data_used_for_check": "teacher-controlled tensor fixtures only; not self/peer training data"
        if plan["study"] == "c"
        else None,
        "bank_dependency": "requires genuine shared checkpoints, collection and matching before C post-training"
        if plan["study"] == "c" and not plan["sealed_bank"]
        else None,
        "colab_run": False,
        "measured_train_throughput": None,
    }
    write_json(output, result)
    return result
