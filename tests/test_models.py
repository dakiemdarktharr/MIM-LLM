import pytest
import torch

from mim_llm.models import ModelConfig, build_model, cross_entropy, parameter_count

torch.set_num_threads(1)
KINDS = (
    "mim",
    "mim_no_n",
    "mim_no_s",
    "mim_no_m",
    "mim_pair",
    "lstm",
    "nested_lstm",
    "gru",
    "mingru",
    "delta_rnn",
    "token_shift",
    "transformer",
)


@pytest.mark.parametrize("kind", KINDS)
def test_causal_and_stepwise_agreement(kind):
    torch.manual_seed(17)
    model = build_model(ModelConfig(kind=kind, width=16, layers=2, context=32)).eval()
    ids = torch.tensor([[1, 24, 35, 40, 2], [1, 99, 71, 34, 2]])
    full, _ = model(ids)
    changed = ids.clone()
    changed[:, 4] = 53
    altered, _ = model(changed)
    torch.testing.assert_close(full[:, :4], altered[:, :4], rtol=1e-5, atol=1e-6)
    state = None
    parts = []
    for time in range(ids.shape[1]):
        logits, _, state = model(
            ids[:, time : time + 1], state=state, return_state=True
        )
        parts.append(logits)
    torch.testing.assert_close(full, torch.cat(parts, dim=1), rtol=1e-5, atol=1e-6)
    loss = cross_entropy(full, ids)
    loss.backward()
    assert parameter_count(model) > 0
    assert all(
        p.grad is not None and torch.isfinite(p.grad).all()
        for p in model.parameters()
        if p.requires_grad
    )


@pytest.mark.parametrize("kind", KINDS)
def test_padded_prefix_matches_unpadded(kind):
    torch.manual_seed(2)
    model = build_model(ModelConfig(kind=kind, width=16, layers=2, context=32)).eval()
    short = torch.tensor([[1, 20, 21]])
    padded = torch.tensor([[1, 20, 21, 0, 0]])
    short_logits, _ = model(short)
    padded_logits, _ = model(padded, torch.tensor([[1, 1, 1, 0, 0]], dtype=torch.bool))
    torch.testing.assert_close(short_logits, padded_logits[:, :3], rtol=1e-5, atol=1e-6)


def test_pair_projection_can_represent_exact_difference():
    model = build_model(ModelConfig(kind="mim_pair", width=8, layers=2))
    with torch.no_grad():
        model.pair.weight.copy_(torch.cat((torch.eye(8), -torch.eye(8)), dim=1))
        model.pair.bias.zero_()
    a, b = torch.randn(3, 8), torch.randn(3, 8)
    torch.testing.assert_close(model.pair(torch.cat((a, b), dim=1)), a - b)


def test_three_layer_cascaded_difference_stepwise():
    model = build_model(
        ModelConfig(kind="mim", width=12, layers=3, difference_mode="cascade")
    ).eval()
    ids = torch.tensor([[1, 10, 11, 12]])
    full, _ = model(ids)
    state, parts = None, []
    for time in range(ids.shape[1]):
        logits, _, state = model(
            ids[:, time : time + 1], state=state, return_state=True
        )
        parts.append(logits)
    torch.testing.assert_close(full, torch.cat(parts, dim=1))


def test_mingru_scan_matches_masked_stepwise_long_sequence():
    torch.manual_seed(31)
    model = build_model(
        ModelConfig(kind="mingru", width=12, layers=2, context=32)
    ).eval()
    ids = torch.randint(3, 80, (2, 17))
    mask = torch.tensor([[1] * 17, [1] * 11 + [0] * 6], dtype=torch.bool)
    full, _ = model(ids, mask)
    state, parts = None, []
    for time in range(ids.shape[1]):
        logits, state, _ = model.step(ids[:, time], state, mask[:, time])
        parts.append(logits[:, None])
    torch.testing.assert_close(full, torch.cat(parts, dim=1), rtol=1e-5, atol=1e-6)


@pytest.mark.training
def test_tiny_batch_loss_falls():
    torch.manual_seed(0)
    model = build_model(ModelConfig(kind="mim", width=12, layers=2, context=12))
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.01)
    ids = torch.tensor([[1, 35, 68, 72, 2], [1, 45, 68, 82, 2]])
    losses = []
    for _ in range(30):
        logits, _ = model(ids[:, :-1])
        loss = cross_entropy(logits, ids[:, 1:])
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach()))
    assert losses[-1] < losses[0] * 0.2


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
@pytest.mark.parametrize("kind", KINDS)
def test_cuda_forward_backward_is_finite(kind):
    model = build_model(ModelConfig(kind=kind, width=16, layers=2, context=16)).cuda()
    ids = torch.tensor([[1, 10, 20, 2], [1, 11, 21, 2]], device="cuda")
    logits, _ = model(ids[:, :-1])
    loss = cross_entropy(logits, ids[:, 1:])
    loss.backward()
    assert torch.isfinite(loss)
    assert all(
        parameter.grad is not None and torch.isfinite(parameter.grad).all()
        for parameter in model.parameters()
        if parameter.requires_grad
    )
