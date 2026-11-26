"""Authorized synthetic optimizer tests; no paper results or real-data fitting."""
# ruff: noqa: F811 -- imported pytest fixture is resolved by the argument name.

import json

import pytest
import torch
from test_foundation import codec, corpus_fixture  # noqa: F401 - pytest fixture

from mim_llm import training_gate
from mim_llm.foundation.corpus import encode_corpus
from mim_llm.foundation.modeling import FoundationConfig, build_foundation
from mim_llm.foundation.objectives import make_batch, selected_ce
from mim_llm.foundation.plan import make_plan
from mim_llm.foundation.runner import execute
from mim_llm.q3a.io import read_rows


@pytest.mark.training
@pytest.mark.parametrize("kind", ["mingru", "transformer"])
def test_foundation_optimizer_stage_transition_and_exact_resume(
    codec, tmp_path, monkeypatch, kind
):
    torch.set_num_threads(2)
    story = "Lan had a key. Mai kept it safe. The door was red. Huy went back home. They all felt happy."
    raw = tmp_path / "corpus.jsonl"
    corpus_fixture(
        raw,
        [
            {"source_id": split, "split": split, "text": story}
            for split in ("train", "validation", "test")
        ],
    )
    encoded = tmp_path / "encoded"
    encode_corpus(raw, encoded, codec, context=256)
    config = {
        "context": 256,
        "pad_id": codec.pad_id,
        "batch_size": 1,
        "grad_clip": 1.0,
        "weight_decay": 0.1,
        "checkpoint_every_updates": 1,
        "stages": [
            {
                "name": name,
                "targets": budget,
                "warmup_targets": 1,
                "learning_rate": 0.01,
                "minimum_lr": 0.001,
            }
            for name, budget in (("lm", 130), ("sft", 50))
        ],
        "models": {
            kind: {
                "vocab_size": codec.vocab_size,
                "embedding_width": 8,
                "width": 10 if kind == "mingru" else 8,
                "layers": 2,
                "heads": 2,
            }
        },
    }
    plan_path = tmp_path / "plan.json"
    plan = make_plan(config, encoded, codec.path, plan_path)
    identifier = f"foundation-{kind}-s0"
    # Only this isolated synthetic test plan; production permission is unchanged.
    policy = tmp_path / "test-only-permission.json"
    policy.write_text(
        json.dumps(
            {
                "model_training_authorized": True,
                "authorized_plan_ids": [plan["plan_id"]],
                "authorized_run_ids": [identifier],
            }
        )
    )
    monkeypatch.setattr(training_gate, "POLICY", policy)
    full = execute(plan_path, identifier, tmp_path / "full", seconds_limit=60)
    first = execute(
        plan_path, identifier, tmp_path / "split", seconds_limit=60, max_updates=1
    )
    assert not first["complete"]
    resumed = execute(
        plan_path, identifier, tmp_path / "split", seconds_limit=60, resume=True
    )
    assert full["complete"] and resumed["complete"]
    assert full["stats"]["targets"] == resumed["stats"]["targets"] == 180
    for name in ("latest.pt", "lm-final.pt", "sft-final.pt", "final.pt"):
        a = torch.load(tmp_path / "full" / identifier / name, weights_only=True)
        b = torch.load(tmp_path / "split" / identifier / name, weights_only=True)
        for key, tensor in a["model"].items():
            torch.testing.assert_close(tensor, b["model"][key], rtol=0, atol=0)
        for key in (
            "stage",
            "targets",
            "input_tokens",
            "stage_targets",
            "updates",
            "epoch",
            "cursor",
        ):
            assert a["stats"][key] == b["stats"][key]
    logs = read_rows(tmp_path / "split" / identifier / "metrics.jsonl")
    assert sum(r["batch_targets"] for r in logs) == 180
    assert {r["stage"] for r in logs} == {"lm", "sft"}
    assert all(torch.isfinite(torch.tensor(r["ce"])) for r in logs)


@pytest.mark.training
@pytest.mark.parametrize("kind", ["mingru", "transformer"])
def test_foundation_tiny_batch_memorization(kind):
    torch.set_num_threads(2)
    torch.manual_seed(0)
    model = build_foundation(
        FoundationConfig(
            kind,
            vocab_size=16,
            embedding_width=16,
            width=24 if kind == "mingru" else 16,
            layers=2,
            heads=2,
            context=16,
        )
    )
    batch = make_batch(
        [{"input_ids": [15, 1, 2, 3], "targets": [1, 2, 3, 15]}], pad_id=15, context=16
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.01, foreach=False)
    first = float(selected_ce(model, batch)[0].detach())
    for _ in range(200):
        optimizer.zero_grad(set_to_none=True)
        loss, _ = selected_ce(model, batch)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
        optimizer.step()
    final = float(selected_ce(model, batch)[0].detach())
    assert final < min(0.05, first / 20), (first, final)
