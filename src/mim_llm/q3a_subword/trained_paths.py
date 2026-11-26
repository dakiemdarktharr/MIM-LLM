"""Read-only numerical checks for learned subword foundation checkpoints.

This is engineering validation, not writing quality, state accuracy or a test
set evaluation. It deliberately lives outside the immutable foundation source.
"""

import hashlib
from pathlib import Path

import torch

from ..foundation.corpus import TokenDataset
from ..foundation.modeling import FoundationConfig, build_foundation
from ..foundation.objectives import make_batch
from ..foundation.plan import load_plan
from ..q3a.io import sha256, source_sha256, write_json


def weights_sha256(model):
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        digest.update(name.encode())
        digest.update(str(value.dtype).encode())
        digest.update(str(tuple(value.shape)).encode())
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def _difference(left, right, active, *, atol, rtol):
    left, right = left[active], right[active]
    finite = bool(torch.isfinite(left).all() and torch.isfinite(right).all())
    return {
        "all_finite": finite,
        "max_abs_error": float((left - right).abs().max()) if finite else None,
        "allclose": finite and bool(torch.allclose(left, right, atol=atol, rtol=rtol)),
    }


@torch.inference_mode()
def check_paths(model, ids, mask, *, atol=1e-4, rtol=1e-4):
    """Compare only valid positions; padded queries are not predictions.

    Future intervention changes every token in the second half while retaining
    shape and masks. Causality is required to be bitwise exact on the first half.
    """
    if (
        ids.ndim != 2
        or ids.shape != mask.shape
        or ids.shape[1] < 2
        or mask.dtype != torch.bool
        or not mask[:, 0].all()
        or (mask[:, 1:] & ~mask[:, :-1]).any()
    ):
        raise ValueError("Require nonempty right-padded token batches")
    prior_mode = model.training
    try:
        model.train()
        training = model.head(model.training_features(ids, mask))
        model.eval()
        dense = model(ids, mask)[0]
        checks = {
            "training_features_vs_dense_eval": _difference(
                training, dense, mask, atol=atol, rtol=rtol
            )
        }
        del training
        cached = model(ids, mask, return_state=True)[0]
        checks["dense_eval_vs_cached_full"] = _difference(
            dense, cached, mask, atol=atol, rtol=rtol
        )
        del cached
        state, step_finite, step_close, maximum = None, True, True, 0.0
        for i in range(ids.shape[1]):
            logits, _, state = model(
                ids[:, i : i + 1], mask[:, i : i + 1], state=state, return_state=True
            )
            active = mask[:, i : i + 1]
            if active.any():
                value = _difference(
                    dense[:, i : i + 1], logits, active, atol=atol, rtol=rtol
                )
                step_finite = step_finite and value["all_finite"]
                step_close = step_close and value["allclose"]
                if value["max_abs_error"] is not None:
                    maximum = max(maximum, value["max_abs_error"])
        del state
        checks["dense_eval_vs_token_step"] = {
            "all_finite": step_finite,
            "allclose": step_close,
            "max_abs_error": maximum if step_finite else None,
        }
        cut = ids.shape[1] // 2
        future = ids.clone()
        future[:, cut:] = (future[:, cut:] + 1) % model.config.vocab_size
        changed = model(future, mask)[0]
        checks["future_edit_vs_past_eval"] = _difference(
            dense[:, :cut], changed[:, :cut], mask[:, :cut], atol=0, rtol=0
        )
        del changed
        # Training uses a separate feature path for selected lexical logits.
        model.train()
        original = model.head(model.training_features(ids, mask))[:, :cut]
        changed = model.head(model.training_features(future, mask))[:, :cut]
        checks["future_edit_vs_past_training_features"] = _difference(
            original, changed, mask[:, :cut], atol=0, rtol=0
        )
        del original, changed
        model.eval()
        reset = model(ids, mask)[0]
        checks["fresh_call_state_reset"] = _difference(
            dense, reset, mask, atol=0, rtol=0
        )
        return {
            "batch": ids.shape[0],
            "time": ids.shape[1],
            "valid_positions": int(mask.sum()),
            "checks": checks,
            "passed": all(v["allclose"] for v in checks.values()),
        }
    finally:
        model.train(prior_mode)


def selected_inputs(plan, device):
    """Three longest validation-LM windows + first full-context train window."""
    validation = TokenDataset(plan["data_dir"], "validation", "lm")
    indices = sorted(
        range(len(validation)), key=lambda i: (-int(validation.index[i, 1]), i)
    )[:3]
    if len(indices) != 3:
        raise ValueError("Require three fixed validation windows")
    rows = [validation[i] for i in indices]
    context = plan["config"]["context"]
    cases = []
    for length in sorted({32, 128, 512, max(len(r["input_ids"]) for r in rows)}):
        if length > context or length > max(len(r["input_ids"]) for r in rows):
            continue
        batch = make_batch(
            [{k: v[:length] for k, v in r.items()} for r in rows],
            pad_id=plan["tokenizer_spec"]["pad_id"],
            context=context,
            device=device,
        )
        cases.append(("validation-lm", indices, batch))
    train = TokenDataset(plan["data_dir"], "train", "lm")
    full = next(
        (i for i in range(len(train)) if int(train.index[i, 1]) == context), None
    )
    if full is None:
        raise ValueError("No real full-context training window; do not synthesize one")
    batch = make_batch(
        [train[full]],
        pad_id=plan["tokenizer_spec"]["pad_id"],
        context=context,
        device=device,
    )
    cases.append(("train-lm", [full], batch))
    return cases


def verify_checkpoint(plan_path, checkpoint, run_id, output, *, device="cpu"):
    """Supports partial parents; never silently skips a missing backbone.

    Call separately for each actual checkpoint available. This receipt cannot
    pass a complete-parent gate or substitute for later final-weight checks.
    """
    if Path(output).exists():
        raise FileExistsError(output)
    plan = load_plan(plan_path)
    run = next((r for r in plan["runs"] if r["id"] == run_id), None)
    if run is None:
        raise ValueError("Unknown foundation run")
    before = sha256(checkpoint)
    saved = torch.load(checkpoint, map_location="cpu", weights_only=True)
    if (
        saved.get("identity", {}).get("plan_id") != plan["plan_id"]
        or saved["identity"].get("run") != run
        or saved["identity"].get("precision") != "float32"
        or saved.get("stats", {}).get("updates", 0) < 1
    ):
        raise ValueError("Need an actual learned checkpoint of the declared run")
    stats, complete = saved["stats"], saved["complete"]
    if device.startswith("cuda"):
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    cfg = FoundationConfig(**plan["models"][run["kind"]]["config"])
    model = build_foundation(cfg, seed=run["seed"]).to(device)
    model.load_state_dict(saved["model"], strict=True)
    del saved
    learned_before = weights_sha256(model)
    checks = []
    for split, indices, batch in selected_inputs(plan, device):
        value = check_paths(model, batch["input_ids"], batch["attention_mask"])
        checks.append({"split": split, "encoded_window_indices": indices, **value})
    unchanged = weights_sha256(model) == learned_before and sha256(checkpoint) == before
    report = {
        "plan_id": plan["plan_id"],
        "run": run,
        "checkpoint_sha256": before,
        "checkpoint_stats": stats,
        "checkpoint_complete": complete,
        "actual_parameters": sum(p.numel() for p in model.parameters()),
        "implementation_sha256": source_sha256(__file__),
        "torch": str(torch.__version__),
        "device": device,
        "gpu": torch.cuda.get_device_name() if device.startswith("cuda") else None,
        "precision": "float32_TF32_disabled",
        "atol": 1e-4,
        "rtol": 1e-4,
        "causality_atol": 0,
        "causality_rtol": 0,
        "optimizer_updates": 0,
        "weights_and_checkpoint_unchanged": unchanged,
        "selection": "three longest encoded validation-LM windows, index tiebreak; first full-context train-LM window",
        "test_access": False,
        "writing_quality_measured": False,
        "checks": checks,
        "passed_in_tested_scope": unchanged
        and bool(checks)
        and all(c["passed"] for c in checks),
    }
    write_json(output, report)
    return report
