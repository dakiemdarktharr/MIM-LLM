"""Authorized engineering memorization fixtures, never scientific findings."""

import pytest
import torch

from mim_llm.models import ModelConfig, build_model
from mim_llm.q3a.objectives import batch_examples, ce_loss


@pytest.mark.training
@pytest.mark.parametrize("kind", ["mingru", "transformer"])
def test_q3a_tiny_batch_memorization(kind):
    torch.set_num_threads(2)
    torch.manual_seed(77)
    model = build_model(
        ModelConfig(kind=kind, width=32, layers=2, context=256, dropout=0.0)
    )
    batch = batch_examples(
        [
            {
                "prompt": "UNIT A: continue. ",
                "reference": "A held it. A waited. It stayed shut.",
            },
            {
                "prompt": "UNIT B: continue. ",
                "reference": "B held it. B opened it. It stayed open.",
            },
        ],
        256,
    )
    opt = torch.optim.AdamW(model.parameters(), lr=0.005)
    initial = float(ce_loss(model, batch)[0].detach())
    for _ in range(100):
        opt.zero_grad(set_to_none=True)
        loss, _ = ce_loss(model, batch)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
    final = float(ce_loss(model, batch)[0].detach())
    assert final < 0.3 and final < initial * 0.1
