"""Probability diagnostics detect real changes without treating logit shifts as changes."""

import importlib.util
from pathlib import Path

import torch


def helper():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts/diagnose_q3a_foundation_precision.py"
    )
    spec = importlib.util.spec_from_file_location("precision_diagnostic", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.distribution_errors


def test_distribution_diagnostic_and_decode_policy_account_for_softmax_shift():
    compare = helper()
    logits = torch.tensor([[[0.0, 1.0, 2.0, 3.0], [3.0, 2.0, 1.0, 0.0]]])
    mask = torch.ones(1, 2, dtype=torch.bool)
    r = compare(logits + 1.0, logits.double(), mask, top_k=2)
    assert r["max_absolute_logit_error"] == 1.0
    assert r["argmax_mismatches"] == 0 and r["max_full_probability_L1"] < 1e-12
    assert r["max_decode_policy_L1"] < 1e-6


def test_distribution_diagnostic_detects_a_changed_winning_token():
    logits = torch.tensor([[[0.0, 1.0, 2.0, 3.0]]])
    r = helper()(
        logits.flip(-1), logits.double(), torch.ones(1, 1, dtype=torch.bool), top_k=2
    )
    assert r["argmax_mismatches"] == 1
    assert r["max_decode_policy_L1"] > 1.0


def test_topk_boundary_diagnostic_retains_discrete_jump_without_optimizer():
    path = Path(__file__).resolve().parents[1] / "scripts/diagnose_q3a_topk_boundary.py"
    spec = importlib.util.spec_from_file_location("topk_diagnostic", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    reference = torch.tensor([[[1.0] * 39 + [1e-7, 0.0]]], dtype=torch.float64)
    actual = reference.float()
    actual[0, 0, 39:] = torch.tensor([0.0, 1e-7])
    before = actual.clone()
    result = module.boundary_rows(actual, reference, torch.ones(1, 1, dtype=torch.bool))
    assert result["positions_over_unchanged_L1_limit"] == 1
    assert result["max_native_policy_L1"] > 1e-4
    row = result["largest_boundary_events"][0]
    assert row["position_batch_time"] == [0, 0]
    assert row["max_logit_error"] < 1e-6
    assert row["only_in_actual_CPU_topk"] == [40]
    assert row["only_in_reference_topk"] == [39]
    assert torch.equal(actual, before)
