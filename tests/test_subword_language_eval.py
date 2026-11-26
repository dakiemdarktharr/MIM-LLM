"""Fictional PPL fixtures, no optimizer, tokenizer fitting or real test access."""
# ruff: noqa: F811 -- imported pytest fixtures are resolved by name.

import math
from pathlib import Path

import pytest
import torch
from test_foundation import codec  # noqa:F401
from test_q3a_subword_evaluation import panel  # noqa:F401

from mim_llm.q3a.io import sha256, write_rows
from mim_llm.q3a_subword import evaluate
from mim_llm.q3a_subword import language_eval as lm


def test_general_text_is_locked_before_corpus_access(panel, tmp_path, monkeypatch):
    plan, paths, _, _ = panel
    monkeypatch.setattr(lm, "load_plan", lambda p: plan)
    with pytest.raises(ValueError, match="locked"):
        lm.general_perplexity(
            "mock", paths[0], split="test", general_corpus=tmp_path / "absent"
        )
    with pytest.raises(ValueError, match="cannot release"):
        lm.general_perplexity(
            "mock", "does-not-exist", phase="foundation", split="test"
        )


def test_general_test_ppl_includes_shared_EOS_and_clusters_long_story_windows(
    panel, tmp_path, monkeypatch
):
    plan, paths, registration, evidence = panel
    plan["config"]["batch_size"] = 2
    corpus = tmp_path / "SYNTHETIC-general.jsonl"
    write_rows(
        corpus,
        [
            {"source_id": "TRAIN", "split": "train", "text": "DO NOT ENCODE TRAIN"},
            {
                "source_id": "VALIDATION",
                "split": "validation",
                "text": "DO NOT ENCODE VAL",
            },
            {"source_id": "SYN-A", "split": "test", "text": "!" * 4100},
            {"source_id": "SYN-B", "split": "test", "text": "hi!"},
        ],
    )
    foundation = {
        "corpus_sha256": sha256(corpus),
        "tokenizer": plan["tokenizer"],
        "tokenizer_spec": plan["tokenizer_spec"],
    }
    for parent in plan["parents"].values():
        parent["foundation_plan"] = "SYNTHETIC-parent-plan"
    monkeypatch.setattr(lm, "load_plan", lambda p: plan)
    monkeypatch.setattr(lm, "load_foundation_plan", lambda p: foundation)
    original = lm.FrozenTokenizer.encode

    def guarded(self, text, **kwargs):
        assert not text.startswith("DO NOT ENCODE")
        return original(self, text, **kwargs)

    monkeypatch.setattr(lm.FrozenTokenizer, "encode", guarded)
    selection = tmp_path / "selection.json"
    evaluate.freeze_selection(
        "mock",
        paths,
        registration,
        selection,
        rationale="SYNTHETIC TEST CONTRACT",
        validation_evidence=[evidence],
    )
    flag = torch.backends.mha.get_fastpath_enabled()
    digest = sha256(paths[0])
    result = lm.general_perplexity(
        "mock",
        paths[0],
        split="test",
        selection=selection,
        general_corpus=corpus,
        draws=100,
    )
    assert (
        result["targets"] == 4104 and result["windows"] == 3 and result["sources"] == 2
    )
    assert result["uncertainty"]["source_clusters"] == 2
    assert result["perplexity"] == pytest.approx(
        math.exp(result["nll_nats_per_target"])
    )
    assert result["EOS_supervised"] and not result["temperature_or_topk_applied"]
    assert (
        torch.backends.mha.get_fastpath_enabled() == flag and sha256(paths[0]) == digest
    )
    assert (
        result["weights_and_checkpoint_unchanged"] and result["optimizer_updates"] == 0
    )
    with pytest.raises(ValueError, match="snapshot"):
        lm.general_perplexity(
            "mock",
            paths[0],
            split="test",
            selection=selection,
            general_corpus=registration,
            draws=100,
        )


def test_foundation_general_validation_requires_complete_parent(
    panel, tmp_path, monkeypatch
):
    plan, paths, _, _ = panel
    original = torch.load(paths[0], weights_only=True)
    run = {"id": "foundation-mingru-s0", "kind": "mingru", "seed": 0}
    foundation = {
        "plan_id": "SYNTHETIC-foundation",
        "runs": [run],
        "models": plan["models"],
        "config": {"batch_size": 2, "stages": [{"targets": 80}, {"targets": 20}]},
        "data_dir": str(tmp_path / "encoded"),
        "data_manifest_sha256": "SYNTHETIC-manifest",
        "corpus_sha256": "SYNTHETIC-corpus",
        "tokenizer": plan["tokenizer"],
        "tokenizer_spec": plan["tokenizer_spec"],
    }
    monkeypatch.setattr(lm, "load_foundation_plan", lambda p: foundation)
    original.update(
        identity={"plan_id": foundation["plan_id"], "run": run, "precision": "float32"},
        stats={"stage": 2, "stage_targets": 0, "targets": 100, "updates": 1},
    )
    checkpoint = tmp_path / "SYNTHETIC-foundation.pt"
    torch.save(original, checkpoint)
    monkeypatch.setattr(
        lm, "TokenDataset", lambda *args: [{"input_ids": [258, 0], "targets": [0, 258]}]
    )
    write_rows(
        Path(foundation["data_dir"]) / "validation-lm.sources.jsonl",
        [{"source_id": "SYNTHETIC-source"}],
    )
    result = lm.general_perplexity("mock", checkpoint, phase="foundation", draws=100)
    assert (
        result["targets"] == 2
        and result["sources"] == 1
        and result["phase"] == "foundation"
    )
    original["complete"] = False
    torch.save(original, checkpoint)
    with pytest.raises(ValueError, match="complete declared"):
        lm.general_perplexity("mock", checkpoint, phase="foundation", draws=100)


def test_source_bootstrap_resamples_weighted_whole_stories():
    rows = [
        {"nll_sum_nats": 1.0, "targets": 1, "windows": 2},
        {"nll_sum_nats": 18.0, "targets": 9, "windows": 1},
    ]
    result = lm.source_interval(rows, draws=100)
    assert result["source_clusters"] == 2 and result["nll_ci95"] == [1.0, 2.0]
    assert result["perplexity_ci95"] == pytest.approx([math.e, math.exp(2)])
