"""Review gate binds real identities and refuses larger or nonfinite drift."""

import copy
import importlib.util
from pathlib import Path

import pytest

from mim_llm.q3a.io import read_json, signature


def checker(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "reviewed_backend", root / "scripts/run_q3a_foundation_reviewed.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.check_review, read_json(
        root / "configs/q3a/foundation_backend_policy.json"
    )


def fixture_proof(policy):
    # Synthetic scalar receipt for gate tests; not a scientific/real approval.
    value = {
        "argmax_mismatches": 0,
        "positions": 1,
        "max_full_probability_L1": 1e-5,
        "max_decode_policy_L1": 1e-5,
    }
    return {
        "plan_id": policy["plan_id"],
        "checkpoint_sha256": "synthetic",
        "optimizer_updates": 0,
        "test_access": False,
        "weights_and_checkpoint_unchanged": True,
        "mha_fastpath_enabled_for_inference": False,
        "implementation_sha256": policy["diagnostic_script_sha256"],
        "temperature": 0.8,
        "top_k": 40,
        "training_flag_check": {
            "loss_bitwise_equal": True,
            "all_parameter_gradients_bitwise_equal": True,
            "targets": 1024,
        },
        "cases": [
            {
                "time": t,
                "FP64_path_checks": {"passed": True},
                "FP32_vs_FP64": {
                    k: copy.deepcopy(value)
                    for k in [
                        "training_features",
                        "dense_eval",
                        "cached_full",
                        "token_step",
                    ]
                },
            }
            for t in [641, 1024]
        ],
    }


def test_backend_review_requires_same_checkpoint_and_training_math(monkeypatch):
    check, policy = checker(monkeypatch)
    proof = fixture_proof(policy)
    check(policy, proof, plan_id=policy["plan_id"], checkpoint_sha256="synthetic")
    with pytest.raises(ValueError, match="same-weight"):
        check(policy, proof, plan_id=policy["plan_id"], checkpoint_sha256="other")
    proof["training_flag_check"]["all_parameter_gradients_bitwise_equal"] = False
    with pytest.raises(ValueError, match="training math"):
        check(policy, proof, plan_id=policy["plan_id"], checkpoint_sha256="synthetic")


@pytest.mark.parametrize("drift", [float("nan"), float("inf"), 0.001])
def test_backend_review_rejects_drift_and_policy_relaxation(monkeypatch, drift):
    check, policy = checker(monkeypatch)
    proof = fixture_proof(policy)
    proof["cases"][0]["FP32_vs_FP64"]["token_step"]["max_decode_policy_L1"] = drift
    with pytest.raises(ValueError, match="drift"):
        check(policy, proof, plan_id=policy["plan_id"], checkpoint_sha256="synthetic")
    policy["probability_L1_limit"] = 1.0
    policy["policy_id"] = signature(
        {k: v for k, v in policy.items() if k != "policy_id"}
    )
    with pytest.raises(ValueError, match="relax"):
        check(
            policy,
            fixture_proof(policy),
            plan_id=policy["plan_id"],
            checkpoint_sha256="synthetic",
        )
