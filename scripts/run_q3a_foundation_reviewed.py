"""Same foundation driver with an explicit, evidence-bound inference backend.

Training code/data/targets are unchanged. A reviewed numerical contract is not
a scientific outcome, a retroactive strict-logit pass, or permission expansion.
"""

import argparse
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path

import torch
from run_q3a_foundation import main as foundation_main

from mim_llm.q3a.io import read_json, sha256, signature, write_json


def check_review(policy, proof, *, plan_id, checkpoint_sha256):
    if (
        signature({k: v for k, v in policy.items() if k != "policy_id"})
        != policy["policy_id"]
    ):
        raise ValueError("Changed backend policy")
    if (
        policy["probability_L1_limit"] != 1e-4
        or policy["reference_tolerance_atol_rtol"] != 1e-10
        or policy["mha_fastpath_enabled"] is not False
        or policy["effective_before_invocation"] != 5
    ):
        raise ValueError("Do not relax the reviewed numerical contract")
    if (
        policy["plan_id"] != plan_id
        or proof["plan_id"] != plan_id
        or proof["checkpoint_sha256"] != checkpoint_sha256
        or proof.get("optimizer_updates") != 0
        or proof.get("test_access") is not False
        or proof.get("weights_and_checkpoint_unchanged") is not True
        or proof.get("mha_fastpath_enabled_for_inference") is not False
        or proof.get("implementation_sha256") != policy["diagnostic_script_sha256"]
        or proof.get("temperature") != 0.8
        or proof.get("top_k") != 40
    ):
        raise ValueError("Missing/changed same-weight numerical proof")
    training = proof["training_flag_check"]
    if (
        training["loss_bitwise_equal"] is not True
        or training["all_parameter_gradients_bitwise_equal"] is not True
        or training["targets"] != 1024
    ):
        raise ValueError("Backend flag has not preserved tested training math")
    if {c["time"] for c in proof["cases"]} != {641, 1024} or len(proof["cases"]) != 2:
        raise ValueError("Incomplete fixed numerical panel")
    for case in proof["cases"]:
        if not case["FP64_path_checks"]["passed"]:
            raise ValueError("High-precision path disagreement")
        if set(case["FP32_vs_FP64"]) != {
            "training_features",
            "dense_eval",
            "cached_full",
            "token_step",
        }:
            raise ValueError("Missing production path")
        for value in case["FP32_vs_FP64"].values():
            if value["argmax_mismatches"] != 0 or value["positions"] < 1:
                raise ValueError("Numerical decision disagreement")
            for key in ("max_full_probability_L1", "max_decode_policy_L1"):
                observed = value[key]
                if (
                    type(observed) not in (int, float)
                    or not math.isfinite(observed)
                    or not 0 <= observed <= policy["probability_L1_limit"]
                ):
                    raise ValueError("Probability drift exceeds prospective contract")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-policy", required=True)
    parser.add_argument("--review-proof", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--drive", required=True)
    parser.add_argument("--wall-seconds", type=int, default=1100)
    parser.add_argument("--resource-annex", required=True)
    a = parser.parse_args()
    policy, proof = read_json(a.backend_policy), read_json(a.review_proof)
    root = Path(a.drive)
    ledger = read_json(root / "foundation-budget.json")
    if len(ledger["invocations"]) < policy["effective_before_invocation"] - 1 or any(
        i["status"] != "finished" for i in ledger["invocations"]
    ):
        raise ValueError("Prior driver must be terminal and reviewed")
    run = proof["run"]["id"]
    if run not in {"foundation-transformer-s0", "foundation-mingru-s0"}:
        raise ValueError("Only existing authorized seed-zero runs")
    checkpoint = root / "runs" / run / "latest.pt"
    check_review(
        policy,
        proof,
        plan_id=read_json(a.plan)["plan_id"],
        checkpoint_sha256=sha256(checkpoint),
    )
    local = Path("artifacts/foundation-runs") / run / "latest.pt"
    if local.exists() and sha256(local) != sha256(checkpoint):
        raise ValueError("Scratch checkpoint differs from reviewed Drive state")
    torch.backends.mha.set_fastpath_enabled(False)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    write_json(
        root / "sessions" / (stamp + "-reviewed-backend.json"),
        {
            "policy_id": policy["policy_id"],
            "policy_sha256": sha256(a.backend_policy),
            "proof_sha256": sha256(a.review_proof),
            "reviewed_checkpoint_sha256": sha256(checkpoint),
            "mha_fastpath_enabled": torch.backends.mha.get_fastpath_enabled(),
            "source_sha256": sha256(__file__),
            "torch": str(torch.__version__),
            "next_invocation": len(ledger["invocations"]) + 1,
            "scientific_or_strict_logit_pass_claimed": False,
        },
    )
    print(
        json.dumps(
            {"backend_policy_id": policy["policy_id"], "mha_fastpath_enabled": False}
        ),
        flush=True,
    )
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
