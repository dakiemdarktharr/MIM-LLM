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
