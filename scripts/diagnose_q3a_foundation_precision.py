"""Diagnose FP32 cache drift against same-weight FP64, without any optimizer.

This does not override failed strict-logit receipts or authorize another run.
Disables the independently isolated MHA inference fastpath in this process only.
"""

import argparse
import json
from pathlib import Path

import torch

from mim_llm.foundation.modeling import FoundationConfig, build_foundation
from mim_llm.foundation.objectives import selected_ce
from mim_llm.foundation.plan import load_plan
from mim_llm.q3a.io import sha256, source_sha256, write_json
from mim_llm.q3a_subword.trained_paths import (
    check_paths,
    selected_inputs,
    weights_sha256,
)


def distribution_errors(actual, reference, mask, *, temperature=0.8, top_k=40):
    """Full-vocabulary probability and exact declared top-k policy comparisons.

    Native FP32 temperature/top-k/softmax is retained for actual generation;
    the reference policy is calculated in FP64 from the promoted weights.
    """
    a, r = actual.detach().cpu()[mask.cpu()], reference.detach().cpu()[mask.cpu()]
    if not torch.isfinite(a).all() or not torch.isfinite(r).all():
        raise FloatingPointError("Nonfinite diagnostic logits")
    result = {
        "positions": len(a),
        "vocabulary": a.shape[-1],
        "max_absolute_logit_error": float((a.double() - r.double()).abs().max()),
        "argmax_mismatches": int((a.argmax(-1) != r.argmax(-1)).sum()),
        "max_full_probability_L1": 0.0,
        "max_decode_policy_L1": 0.0,
        "max_KL_reference_to_actual": 0.0,
    }
    for i in range(0, len(a), 8):
        left, right = a[i : i + 8], r[i : i + 8].double()
        logp, logq = left.double().log_softmax(-1), right.log_softmax(-1)
        result["max_full_probability_L1"] = max(
            result["max_full_probability_L1"],
            float((logp.exp() - logq.exp()).abs().sum(-1).max()),
        )
        result["max_KL_reference_to_actual"] = max(
            result["max_KL_reference_to_actual"],
            float((logq.exp() * (logq - logp)).sum(-1).max()),
        )
        # Compare precisely the generation policy, not only untruncated softmax.
        pv, pi = (left.float() / temperature).topk(min(top_k, left.shape[-1]), -1)
        qv, qi = (right / temperature).topk(min(top_k, right.shape[-1]), -1)
        p = torch.zeros_like(right).scatter(-1, pi, pv.softmax(-1).double())
        q = torch.zeros_like(right).scatter(-1, qi, qv.softmax(-1))
        result["max_decode_policy_L1"] = max(
            result["max_decode_policy_L1"], float((p - q).abs().sum(-1).max())
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("plan", "checkpoint", "run-id", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    if Path(args.output).exists():
        raise FileExistsError(args.output)
    torch.set_num_threads(2)
    torch.backends.mha.set_fastpath_enabled(False)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    plan = load_plan(args.plan)
    run = next(r for r in plan["runs"] if r["id"] == args.run_id)
    digest = sha256(args.checkpoint)
    saved = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    if (
        saved["identity"]["plan_id"] != plan["plan_id"]
        or saved["identity"]["run"] != run
        or saved["identity"]["precision"] != "float32"
        or saved["stats"]["updates"] < 1
    ):
        raise ValueError("Require the declared actually learned FP32 checkpoint")
    cfg = FoundationConfig(**plan["models"][run["kind"]]["config"])
    actual = build_foundation(cfg).to(args.device)
    reference = build_foundation(cfg).double()
    actual.load_state_dict(saved["model"], strict=True)
    reference.load_state_dict(saved["model"], strict=True)
    del saved
    before = weights_sha256(actual), weights_sha256(reference)
    cases, training_check = [], None
    for split, indices, batch in selected_inputs(plan, args.device):
        if batch["input_ids"].shape[1] < 641:
            continue
        ids, mask = batch["input_ids"], batch["attention_mask"]
        with torch.inference_mode():
            ref_paths = check_paths(
                reference, ids.cpu(), mask.cpu(), atol=1e-10, rtol=1e-10
            )
            reference.eval()
            expected = reference(ids.cpu(), mask.cpu())[0]
            actual.train()
            training = actual.head(actual.training_features(ids, mask))
            values = {
                "training_features": distribution_errors(training, expected, mask)
            }
            del training
            actual.eval()
            dense = actual(ids, mask)[0]
            values["dense_eval"] = distribution_errors(dense, expected, mask)
            del dense
            cached = actual(ids, mask, return_state=True)[0]
            values["cached_full"] = distribution_errors(cached, expected, mask)
            del cached
            state, parts = None, []
            for i in range(ids.shape[1]):
                logits, _, state = actual(
                    ids[:, i : i + 1],
                    mask[:, i : i + 1],
                    state=state,
                    return_state=True,
                )
                parts.append(logits)
            step = torch.cat(parts, 1)
            values["token_step"] = distribution_errors(step, expected, mask)
            del step, parts, state, expected
        cases.append(
            {
                "split": split,
                "indices": indices,
                "time": ids.shape[1],
                "FP64_path_checks": ref_paths,
                "FP32_vs_FP64": values,
            }
        )
        if split == "train-lm":
            # A controlled nonupdating backward check: does the inference flag
            # alter the actual selected-head training objective/gradients?
            actual.train()
            gradients, losses = [], []
            for enabled in (True, False):
                torch.backends.mha.set_fastpath_enabled(enabled)
                actual.zero_grad(set_to_none=True)
                loss, n = selected_ce(actual, batch)
                loss.backward()
                losses.append(float(loss.detach()))
                gradients.append(
                    {
                        k: p.grad.detach().cpu().clone()
                        for k, p in actual.named_parameters()
                    }
                )
            training_check = {
                "targets": n,
                "losses_fastpath_enabled_disabled": losses,
                "loss_bitwise_equal": losses[0] == losses[1],
                "all_parameter_gradients_bitwise_equal": all(
                    torch.equal(gradients[0][k], gradients[1][k]) for k in gradients[0]
                ),
            }
            actual.zero_grad(set_to_none=True)
            torch.backends.mha.set_fastpath_enabled(False)
    result = {
        "purpose": "numerical diagnosis only; does not override failed strict receipts or authorize training",
        "plan_id": plan["plan_id"],
        "run": run,
        "checkpoint_sha256": digest,
        "implementation_sha256": source_sha256(__file__),
        "torch": str(torch.__version__),
        "device": args.device,
        "gpu": torch.cuda.get_device_name() if args.device.startswith("cuda") else None,
        "reference": "FP64 CPU, same promoted learned FP32 weights",
        "mha_fastpath_enabled_for_inference": False,
        "temperature": 0.8,
        "top_k": 40,
        "optimizer_updates": 0,
        "test_access": False,
        "weights_and_checkpoint_unchanged": before
        == (weights_sha256(actual), weights_sha256(reference))
        and digest == sha256(args.checkpoint),
        "training_flag_check": training_check,
        "cases": cases,
    }
    write_json(args.output, result)
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}), flush=True)
    for c in cases:
        print(
            json.dumps({k: v for k, v in c.items() if k != "FP64_path_checks"}),
            flush=True,
        )


if __name__ == "__main__":
    main()
