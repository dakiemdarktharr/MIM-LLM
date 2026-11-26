"""Useful fail-closed path-check tests, without optimizer steps or tokenizer fit."""

import pytest
import torch
from test_foundation import model_for

from mim_llm.q3a_subword.trained_paths import check_paths, weights_sha256


def inputs():
    ids = torch.tensor([[258, 0, 7, 2, 4, 9], [258, 4, 3, 258, 258, 258]])
    mask = torch.tensor([[1, 1, 1, 1, 1, 1], [1, 1, 1, 0, 0, 0]], dtype=torch.bool)
    return ids, mask


@pytest.mark.parametrize("kind", ["mingru", "transformer"])
def test_readonly_checker_compares_real_paths_and_restores_mode(kind):
    model = model_for(kind).train()
    before = weights_sha256(model)
    result = check_paths(model, *inputs())
    assert result["passed"] and result["valid_positions"] == 9
    assert model.training and weights_sha256(model) == before
    assert result["checks"]["future_edit_vs_past_eval"]["max_abs_error"] == 0
    assert (
        result["checks"]["future_edit_vs_past_training_features"]["max_abs_error"] == 0
    )
    assert all(p.grad is None for p in model.parameters())


def test_checker_detects_a_corrupt_cached_path():
    model = model_for("transformer").eval()
    original = model.forward

    def corrupt(*args, **kwargs):
        result = original(*args, **kwargs)
        return (result[0] + 0.25, *result[1:]) if kwargs.get("return_state") else result

    model.forward = corrupt
    result = check_paths(model, *inputs())
    assert not result["passed"] and not model.training
    assert not result["checks"]["dense_eval_vs_cached_full"]["allclose"]


def test_checker_detects_future_leak_and_rejects_nonprefix_mask():
    model = model_for("mingru").eval()
    original = model.forward

    def leak(ids, *args, **kwargs):
        result = original(ids, *args, **kwargs)
        return (result[0] + ids[:, -1, None, None].float(), *result[1:])

    model.forward = leak
    result = check_paths(model, *inputs())
    assert not result["checks"]["future_edit_vs_past_eval"]["allclose"]
    ids, mask = inputs()
    mask[0, 1] = False
    with pytest.raises(ValueError, match="right-padded"):
        check_paths(model, ids, mask)
