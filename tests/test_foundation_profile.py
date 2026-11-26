"""The profiling helper computes gradients but must never optimize weights."""

import importlib.util
from pathlib import Path

import pytest
from test_foundation import model_for

from mim_llm.foundation.objectives import make_batch

spec = importlib.util.spec_from_file_location(
    "foundation_profile",
    Path(__file__).resolve().parents[1] / "scripts/profile_q3a_foundation.py",
)
profile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profile)


@pytest.mark.parametrize("kind", ["mingru", "transformer"])
def test_forward_backward_probe_preserves_all_parameters(kind):
    model = model_for(kind)
    batch = make_batch(
        [{"input_ids": [258, 0, 1, 2], "targets": [-100, 1, 2, 258]}],
        pad_id=258,
        context=64,
    )
    result = profile.probe_batches(model, [batch, batch], device="cpu")
    assert result["learned_parameters_unchanged"] is True
    assert result["optimizer_updates"] == 0 and result["targets"] == 6
    assert result["seconds"] > 0
    assert all(p.grad is None for p in model.parameters())
