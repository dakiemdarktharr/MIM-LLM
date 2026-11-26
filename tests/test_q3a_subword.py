"""Subword prompt/response and auxiliary-probe tests, without optimizer updates."""
# ruff: noqa: F811 -- imported pytest fixture is resolved by argument name.

import copy

import pytest
import torch
from test_foundation import codec  # noqa: F401

from mim_llm.foundation.modeling import FoundationConfig, build_foundation
from mim_llm.foundation.objectives import make_batch
from mim_llm.q3a.objectives import js_divergence
from mim_llm.q3a_subword.objectives import batch_examples, ce_loss, probe_js, probe_rows


def bundle():
    world = {
        "initial_holder": "Lan",
        "transfers": ["Mai"],
        "permission": True,
        "power_return": 1,
        "deadline": 5,
    }
    return {
        "scenarios": {
            "base": {"prompt": "Power returned at 08:55.\n", "world": world},
            "noop": {
                "prompt": "Power returned at 08:56.\n",
                "world": {**world, "power_return": 2},
            },
        }
    }


def test_subword_response_ce_budget_eos_and_context(codec):
    torch.set_num_threads(2)
    model = build_foundation(
        FoundationConfig(
            "mingru", vocab_size=259, embedding_width=8, width=10, layers=2, context=256
        )
    )
    rows = [{"prompt": "Story:\n", "reference": "hi!"}] * 2
    batch = batch_examples(rows, codec, 256)
    loss, count = ce_loss(model, batch)
    assert count == 2 * len(codec.encode("hi!", eos=True))
    assert torch.isfinite(loss) and loss.requires_grad
    limited = batch_examples(rows, codec, 256, remaining=2)
    assert int((limited["targets"] != -100).sum()) == 2
    with pytest.raises(ValueError, match="boundary"):
        batch_examples([{"prompt": "Answer: ", "reference": "hi!"}], codec, 256)
    with pytest.raises(ValueError, match="context"):
        batch_examples(rows, codec, 2)


@pytest.mark.parametrize("kind", ["mingru", "transformer"])
def test_selected_probe_js_equals_dense_loss_and_gradients(codec, kind):
    torch.set_num_threads(2)
    torch.manual_seed(0)
    model = build_foundation(
        FoundationConfig(
            kind,
            vocab_size=259,
            embedding_width=8,
            width=10 if kind == "mingru" else 8,
            layers=2,
            heads=2,
            context=256,
        )
    )
    b = bundle()
    rows = probe_rows(codec, b, 256)
    batch = make_batch(rows, pad_id=codec.pad_id, context=256)
    logits = model(batch["input_ids"], batch["attention_mask"])[0]
    dense = js_divergence(*[logits[i, batch["targets"][i] != -100] for i in range(2)])
    dense.backward()
    gradients = {k: p.grad.clone() for k, p in model.named_parameters()}
    model.zero_grad(set_to_none=True)
    selected, metadata = probe_js(model, codec, b, 256)
    selected.backward()
    torch.testing.assert_close(dense, selected, atol=1e-6, rtol=1e-4)
    for k, parameter in model.named_parameters():
        torch.testing.assert_close(parameter.grad, gradients[k], atol=1e-6, rtol=1e-4)
    assert metadata["probe_positions"] == 2 * len(codec.encode("Mai", eos=True))
    assert metadata["inference_state_table"] is False
    changed = copy.deepcopy(b)
    changed["scenarios"]["noop"]["world"]["transfers"] = ["Huy"]
    with pytest.raises(ValueError, match="target"):
        probe_rows(codec, changed, 256)


def test_all_probe_answers_have_stable_newline_boundary(codec):
    for key in ("holder", "action", "cabinet", "power_available", "permission"):
        rows = probe_rows(codec, bundle(), 256, key)
        assert rows[0]["targets"] == rows[1]["targets"]
        assert rows[0]["targets"][-1] == codec.eos_id
