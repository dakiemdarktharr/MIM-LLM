"""Fictional backend checks, no optimization or real model outputs."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from mim_llm.q3a_subword import inference


class FixedModel(torch.nn.Module):
    def __init__(self, scores):
        super().__init__()
        self.scores = torch.nn.Parameter(torch.tensor(scores, dtype=torch.float64))
        self.config = SimpleNamespace(context=32)

    def forward(self, ids, *, state=None, return_state=False):
        logits = self.scores.expand(*ids.shape, -1)
        return (logits, None, {}) if return_state else (logits, None)


class Codec:
    eos_id = bos_id = pad_id = 2

    def encode(self, text, **kwargs):
        return [2]

    def decode(self, ids):
        return str(ids)


def test_canonical_policy_has_stable_ID_ties_and_no_FP32_cast():
    scores = torch.tensor([[1.0, 1.0, 1.0]], dtype=torch.float64)
    probabilities, ids = inference.topk_distribution(scores, top_k=2)
    assert ids.tolist() == [[0, 1]]
    assert probabilities.dtype == torch.float64
    scores[0, 1] += 1e-9
    _, ids = inference.topk_distribution(scores, top_k=1)
    assert ids.tolist() == [[1]]
    with pytest.raises(ValueError, match="CPU/FP64"):
        inference.topk_distribution(scores.float())


def test_canonical_generation_keeps_precision_EOS_cap_and_flags():
    model = FixedModel([1.0, 1.0 + 1e-9, 0.0])
    flag = torch.backends.mha.get_fastpath_enabled()
    threads = torch.get_num_threads()
    result = inference.generate(model, Codec(), "FICTIONAL", max_new_tokens=3, top_k=1)
    assert result["token_ids"] == [1, 1, 1] and result["cap_reached"]
    assert result["inference_backend"] == inference.BACKEND
    assert torch.backends.mha.get_fastpath_enabled() == flag
    assert torch.get_num_threads() == threads
    assert inference.generate(
        FixedModel([0.0, 0.0, 10.0]), Codec(), "FIXTURE", top_k=1, max_new_tokens=3
    )["eos_emitted"]
    with pytest.raises(ValueError, match="CPU/FP64"):
        inference.generate(model.float(), Codec(), "FICTIONAL")


def test_FP64_distribution_diagnosis_rejects_precision_and_detects_corruption():
    path = (
        Path(__file__).resolve().parents[1] / "scripts/diagnose_q3a_fp64_inference.py"
    )
    spec = importlib.util.spec_from_file_location("FP64_diagnostic", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    scores = torch.tensor([[[0.0, 1.0, 2.0, 3.0]]], dtype=torch.float64)
    mask = torch.ones(1, 1, dtype=torch.bool)
    result = module.distribution_errors(scores.flip(-1), scores, mask)
    assert result["argmax_mismatches"] == 1 and result["max_decode_policy_L1"] > 1
    with pytest.raises(ValueError, match="downcast"):
        module.distribution_errors(scores.float(), scores, mask)
