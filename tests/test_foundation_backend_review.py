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


def test_FP64_replacement_keeps_limits_and_same_checkpoint_proof_chain(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "FP64_reviewed_backend", root / "scripts/run_q3a_foundation_fp64_reviewed.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    policy = read_json(root / "configs/q3a/foundation_fp64_backend_policy.json")
    prior = fixture_proof(
        read_json(root / "configs/q3a/foundation_backend_policy.json")
    )
    # Keep a synthetic failed old receipt: a replacement must not rewrite it.
    prior["cases"][0]["FP32_vs_FP64"]["dense_eval"]["max_decode_policy_L1"] = 0.0057
    proof = {
        **copy.deepcopy(prior),
        "original_FP32_proof_sha256": "SYNTHETIC-prior",
        "implementation_sha256": policy["diagnostic_script_sha256"],
        "inference_source_sha256": policy["inference_source_sha256"],
        "backend": policy["backend"],
        "device": "cpu",
        "precision": "float64",
        "original_checkpoint_precision": "float32",
        "mha_fastpath_enabled": False,
        "cases": [
            {
                "split": split,
                "time": t,
                "path_checks": {"passed": True},
                "production_vs_reference": copy.deepcopy(
                    prior["cases"][1]["FP32_vs_FP64"]
                ),
            }
            for split, t in [("validation-lm", 641), ("train-lm", 1024)]
        ],
    }
    args = {
        "plan_id": policy["plan_id"],
        "checkpoint_sha256": "synthetic",
        "prior_sha256": "SYNTHETIC-prior",
    }
    module.check_review(policy, proof, prior, **args)
    assert (
        prior["cases"][0]["FP32_vs_FP64"]["dense_eval"]["max_decode_policy_L1"]
        == 0.0057
    )
    with pytest.raises(ValueError, match="proof chain"):
        module.check_review(
            policy, proof, prior, **{**args, "checkpoint_sha256": "other"}
        )
    broken = copy.deepcopy(proof)
    broken["cases"][0]["production_vs_reference"]["token_step"][
        "max_decode_policy_L1"
    ] = 0.0057
    with pytest.raises(ValueError, match="unchanged"):
        module.check_review(policy, broken, prior, **args)
    relaxed = {**policy, "probability_L1_limit": 0.01}
    relaxed["policy_id"] = signature(
        {k: v for k, v in relaxed.items() if k != "policy_id"}
    )
    with pytest.raises(ValueError, match="relax"):
        module.check_review(relaxed, proof, prior, **args)
