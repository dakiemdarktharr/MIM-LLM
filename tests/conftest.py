"""Default test runs cannot optimize weights or fit tokenizers."""

import pytest
import torch


@pytest.fixture(autouse=True)
def prohibit_unmarked_training(request, monkeypatch):
    if request.node.get_closest_marker("training"):
        from mim_llm.training_gate import require_training_permission

        require_training_permission("model", "pytest:" + request.node.nodeid)
        return

    def denied(*args, **kwargs):
        raise AssertionError("Optimizer steps are forbidden in non-training tests")

    for name in ("AdamW", "Adam", "SGD", "RMSprop", "Adagrad"):
        monkeypatch.setattr(getattr(torch.optim, name), "step", denied)
    try:
        import sentencepiece as spm

        monkeypatch.setattr(spm.SentencePieceTrainer, "train", denied)
    except ImportError:
        pass
