"""Unchanged FP32 foundation training after a separately reviewed FP64 fix.

Old FP32 receipts stay failed; thresholds are not enlarged. The canonical
CPU/FP64 generator is used uniformly for future writing/primary evaluation.
"""

import argparse
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path

import torch
from run_q3a_foundation import main as foundation_main

from mim_llm.q3a.io import read_json, sha256, signature, source_sha256, write_json
from mim_llm.q3a_subword import inference


def check_review(policy, proof, prior, *, plan_id, checkpoint_sha256, prior_sha256):
    if (
        signature({k: v for k, v in policy.items() if k != "policy_id"})
        != policy["policy_id"]
    ):
        raise ValueError("Changed higher precision policy")
    if (
        policy["effective_before_invocation"] != 7
        or policy["probability_L1_limit"] != 1e-4
        or policy["reference_tolerance_atol_rtol"] != 1e-10
        or policy["argmax_mismatches_allowed"] != 0
        or policy["backend"] != inference.BACKEND
        or policy["inference_source_sha256"] != source_sha256(inference.__file__)
        or policy["plan_id"] != plan_id
    ):
        raise ValueError("Do not relax the limits or silently change the backend")
    if (
        proof["plan_id"] != plan_id
        or proof["checkpoint_sha256"] != checkpoint_sha256
        or proof["original_FP32_proof_sha256"] != prior_sha256
        or proof["implementation_sha256"] != policy["diagnostic_script_sha256"]
        or proof["inference_source_sha256"] != policy["inference_source_sha256"]
        or proof["backend"] != inference.BACKEND
        or proof["device"] != "cpu"
        or proof["precision"] != "float64"
        or proof["original_checkpoint_precision"] != "float32"
        or proof["temperature"] != 0.8
        or proof["top_k"] != 40
        or proof["optimizer_updates"] != 0
        or proof["test_access"] is not False
        or proof["weights_and_checkpoint_unchanged"] is not True
        or proof["mha_fastpath_enabled"] is not False
        or prior["checkpoint_sha256"] != checkpoint_sha256
        or prior["plan_id"] != plan_id
        or prior["implementation_sha256"] != policy["prior_diagnostic_script_sha256"]
        or prior["optimizer_updates"] != 0
        or prior["test_access"] is not False
        or prior["weights_and_checkpoint_unchanged"] is not True
        or proof["training_flag_check"] != prior["training_flag_check"]
    ):
        raise ValueError("Incomplete same-checkpoint proof chain")
    training = proof["training_flag_check"]
    if (
        training["targets"] != 1024
        or training["loss_bitwise_equal"] is not True
        or training["all_parameter_gradients_bitwise_equal"] is not True
    ):
        raise ValueError("Actual FP32 training math must be unchanged")
    if len(proof["cases"]) != 2 or {
        (c["split"], c["time"]) for c in proof["cases"]
    } != {("validation-lm", 641), ("train-lm", 1024)}:
        raise ValueError("Incomplete fixed numerical panel")
    for case in proof["cases"]:
        if not case["path_checks"]["passed"]:
            raise ValueError("FP64 path/causality/reset check failed")
        if set(case["production_vs_reference"]) != {
            "training_features",
            "dense_eval",
            "cached_full",
            "token_step",
        }:
            raise ValueError("Missing production path")
        for value in case["production_vs_reference"].values():
            if value["argmax_mismatches"] != 0 or value["positions"] < 1:
                raise ValueError("Numerical decision mismatch")
            for key in ("max_full_probability_L1", "max_decode_policy_L1"):
                metric = value[key]
                if (
                    type(metric) not in (int, float)
                    or not math.isfinite(metric)
                    or not 0 <= metric <= 1e-4
                ):
                    raise ValueError(
                        "Replacement backend exceeds unchanged probability bound"
                    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in (
        "backend-policy",
        "review-proof",
        "fp32-proof",
        "plan",
        "drive",
        "resource-annex",
    ):
        parser.add_argument("--" + key, required=True)
    parser.add_argument("--wall-seconds", type=int, default=1100)
    a = parser.parse_args()
    policy, proof, prior = (
        read_json(a.backend_policy),
        read_json(a.review_proof),
        read_json(a.fp32_proof),
    )
    root = Path(a.drive)
    ledger = read_json(root / "foundation-budget.json")
    if len(ledger["invocations"]) < 6 or any(
        i["status"] != "finished" for i in ledger["invocations"]
    ):
        raise ValueError("Previous driver must be terminal and audited")
    run = proof["run"]["id"]
    if run not in {"foundation-transformer-s0", "foundation-mingru-s0"}:
        raise ValueError("Only authorized seed-zero foundation runs")
    checkpoint = root / "runs" / run / "latest.pt"
    check_review(
        policy,
        proof,
        prior,
        plan_id=read_json(a.plan)["plan_id"],
        checkpoint_sha256=sha256(checkpoint),
        prior_sha256=sha256(a.fp32_proof),
    )
    local = Path("artifacts/foundation-runs") / run / "latest.pt"
    if local.exists() and sha256(local) != sha256(checkpoint):
        raise ValueError("Scratch state differs from reviewed Drive state")
    torch.backends.mha.set_fastpath_enabled(False)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    receipt = {
        "policy_id": policy["policy_id"],
        "policy_sha256": sha256(a.backend_policy),
        "proof_sha256": sha256(a.review_proof),
        "original_FP32_proof_sha256": sha256(a.fp32_proof),
        "reviewed_checkpoint_sha256": sha256(checkpoint),
        "inference_backend": inference.BACKEND,
        "mha_fastpath_enabled": False,
        "source_sha256": sha256(__file__),
        "torch": str(torch.__version__),
        "next_invocation": len(ledger["invocations"]) + 1,
        "training_precision_unchanged": "float32",
        "old_FP32_failures_remain_failed": True,
    }
    write_json(root / "sessions" / (stamp + "-fp64-reviewed-backend.json"), receipt)
    print(json.dumps(receipt), flush=True)
    sys.argv = [
        "run_q3a_foundation.py",
        "--plan",
        a.plan,
        "--drive",
        a.drive,
        "--wall-seconds",
        str(a.wall_seconds),
        "--resource-annex",
        a.resource_annex,
    ]
    foundation_main()


if __name__ == "__main__":
    main()
