"""Higher precision replacement diagnosis; old FP32 failures remain failures."""

import argparse
import json
from pathlib import Path

import torch

from mim_llm.foundation.modeling import FoundationConfig, build_foundation
from mim_llm.foundation.plan import load_plan
from mim_llm.q3a.io import sha256, source_sha256, write_json
from mim_llm.q3a_subword import inference
from mim_llm.q3a_subword.trained_paths import (
    check_paths,
    selected_inputs,
    weights_sha256,
)


def distribution_errors(actual, reference, mask):
    a, r = actual[mask], reference[mask]
    if a.dtype != torch.float64 or r.dtype != torch.float64:
        raise ValueError("Do not silently downcast the replacement backend")
    result = {
        "positions": len(a),
        "argmax_mismatches": int((a.argmax(-1) != r.argmax(-1)).sum()),
        "max_full_probability_L1": 0.0,
        "max_decode_policy_L1": 0.0,
    }
    for i in range(0, len(a), 8):
        left, right = a[i : i + 8], r[i : i + 8]
        lp, li = inference.topk_distribution(left)
        rp, ri = inference.topk_distribution(right)
        p = torch.zeros_like(left).scatter(-1, li, lp)
        q = torch.zeros_like(right).scatter(-1, ri, rp)
        result["max_full_probability_L1"] = max(
            result["max_full_probability_L1"],
            float((left.softmax(-1) - right.softmax(-1)).abs().sum(-1).max()),
        )
        result["max_decode_policy_L1"] = max(
            result["max_decode_policy_L1"], float((p - q).abs().sum(-1).max())
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("plan", "checkpoint", "run-id", "prior-proof", "output"):
        parser.add_argument("--" + key, required=True)
    a = parser.parse_args()
    if Path(a.output).exists():
        raise FileExistsError(a.output)
    plan = load_plan(a.plan)
    run = next(r for r in plan["runs"] if r["id"] == a.run_id)
    digest = sha256(a.checkpoint)
    saved = torch.load(a.checkpoint, map_location="cpu", weights_only=True)
    if (
        saved["identity"]["plan_id"] != plan["plan_id"]
        or saved["identity"]["run"] != run
    ):
        raise ValueError("Wrong learned FP32 checkpoint")
    if any(
        v.is_floating_point() and v.dtype != torch.float32
        for v in saved["model"].values()
    ):
        raise ValueError("Original checkpoint must remain FP32")
    prior = json.loads(Path(a.prior_proof).read_text())
    if (
        prior["checkpoint_sha256"] != digest
        or prior["plan_id"] != plan["plan_id"]
        or prior["optimizer_updates"] != 0
        or prior["weights_and_checkpoint_unchanged"] is not True
    ):
        raise ValueError("Same-checkpoint prior diagnostic required")
    cfg = FoundationConfig(**plan["models"][run["kind"]]["config"])
    model = build_foundation(cfg).double().cpu()
    model.load_state_dict(saved["model"], strict=True)
    del saved
    before = weights_sha256(model)
    cases = []
    with inference.canonical_backend(), torch.inference_mode():
        for split, indices, batch in selected_inputs(plan, "cpu"):
            if batch["input_ids"].shape[1] < 641:
                continue
            ids, mask = batch["input_ids"], batch["attention_mask"]
            checks = check_paths(model, ids, mask, atol=1e-10, rtol=1e-10)
            model.eval()
            reference = model(ids, mask)[0]
            model.train()
            training = model.head(model.training_features(ids, mask))
            values = {
                "training_features": distribution_errors(training, reference, mask),
                "dense_eval": distribution_errors(reference, reference, mask),
            }
            del training
            model.eval()
            cached = model(ids, mask, return_state=True)[0]
            values["cached_full"] = distribution_errors(cached, reference, mask)
            del cached
            state, parts = None, []
            for t in range(ids.shape[1]):
                logits, _, state = model(
                    ids[:, t : t + 1],
                    mask[:, t : t + 1],
                    state=state,
                    return_state=True,
                )
                parts.append(logits)
            values["token_step"] = distribution_errors(
                torch.cat(parts, 1), reference, mask
            )
            del parts, state, reference
            cases.append(
                {
                    "split": split,
                    "indices": indices,
                    "time": ids.shape[1],
                    "path_checks": checks,
                    "production_vs_reference": values,
                }
            )
    result = {
        "purpose": "Replacement backend numerical evidence; no scientific quality claim",
        "plan_id": plan["plan_id"],
        "run": run,
        "checkpoint_sha256": digest,
        "backend": inference.BACKEND,
        "precision": "float64",
        "device": "cpu",
        "torch": str(torch.__version__),
        "mha_fastpath_enabled": False,
        "temperature": 0.8,
        "top_k": 40,
        "optimizer_updates": 0,
        "test_access": False,
        "weights_and_checkpoint_unchanged": before == weights_sha256(model)
        and digest == sha256(a.checkpoint),
        "original_checkpoint_precision": "float32",
        "original_FP32_proof_sha256": sha256(a.prior_proof),
        "training_flag_check": prior["training_flag_check"],
        "implementation_sha256": source_sha256(__file__),
        "inference_source_sha256": source_sha256(inference.__file__),
        "cases": cases,
    }
    write_json(a.output, result)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
