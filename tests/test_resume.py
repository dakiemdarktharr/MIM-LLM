import importlib
from pathlib import Path

import pytest
import torch

from mim_llm.evaluation import write_jsonl
from mim_llm.models import ModelConfig


@pytest.mark.training
def test_interrupted_training_resumes_same_weights(tmp_path, monkeypatch):
    training = importlib.import_module("mim_llm.train")
    corpus = tmp_path / "stories.jsonl"
    write_jsonl(
        corpus,
        [
            {
                "source_id": "a",
                "split": "train",
                "text": "Lan passed the key to Huy. Huy waited.",
            },
            {
                "source_id": "b",
                "split": "train",
                "text": "Mai opened the box after power returned.",
            },
            {
                "source_id": "c",
                "split": "validation",
                "text": "The cabinet stayed closed at nine.",
            },
        ],
    )
    config = ModelConfig(kind="mim", width=8, layers=2, context=8, dropout=0.1)
    kwargs = {
        "seed": 9,
        "batch_size": 2,
        "max_train_tokens": 48,
        "device": "cpu",
        "checkpoint_every_updates": 1,
    }
    original_replace = training.os.replace
    interrupted = {"done": False}

    def interrupt_after_checkpoint(source, destination):
        original_replace(source, destination)
        if Path(destination).name == "latest.pt" and not interrupted["done"]:
            interrupted["done"] = True
            raise RuntimeError("simulated process interruption")

    monkeypatch.setattr(training.os, "replace", interrupt_after_checkpoint)
    with pytest.raises(RuntimeError, match="simulated"):
        training.train(corpus, tmp_path / "resumed", config, **kwargs)
    monkeypatch.setattr(training.os, "replace", original_replace)
    resumed = training.train(
        corpus, tmp_path / "resumed", config, resume=True, **kwargs
    )
    full = training.train(corpus, tmp_path / "full", config, **kwargs)
    assert resumed["train_tokens_actual"] == full["train_tokens_actual"]
    assert resumed["updates"] == full["updates"]
    resumed_state = torch.load(tmp_path / "resumed" / "best.pt", weights_only=True)[
        "model"
    ]
    full_state = torch.load(tmp_path / "full" / "best.pt", weights_only=True)["model"]
    for key in full_state:
        torch.testing.assert_close(resumed_state[key], full_state[key], rtol=0, atol=0)
