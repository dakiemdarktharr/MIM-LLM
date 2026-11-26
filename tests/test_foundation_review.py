"""Review provenance/completion gates; synthetic fixtures, no training."""
# ruff: noqa: F811 -- imported pytest fixture is resolved by argument name.

import copy
import hashlib

import pytest
import torch
from test_foundation import codec  # noqa: F401

from mim_llm.foundation.modeling import FoundationConfig, build_foundation
from mim_llm.q3a.io import read_json, read_rows, signature, source_sha256, write_json
from mim_llm.q3a_subword import foundation_review as review


def panel_fixture():
    text = "Lan found a key. She gave it to Mai. Mai kept it safe."
    prompt = "Lan found a key. She gave it to Mai.\nContinue this story in three to five sentences.\nContinuation:\n"
    digest = hashlib.sha256(prompt.encode()).hexdigest()
    rows = [
        {"source_id": f"v{i}", "split": "validation", "text": text} for i in range(16)
    ]
    recipe = {
        "sources": [
            {"source_id": r["source_id"], "prompt_sha256": digest} for r in rows
        ]
    }
    return rows, recipe


def test_review_retains_all_fixed_sources_without_test_fallback():
    rows, recipe = panel_fixture()
    prompts = review.fixed_prompts(recipe, rows)
    assert len(prompts) == 17
    assert [p["source_id"] for p in prompts[:16]] == [r["source_id"] for r in rows]
    assert prompts[-1]["condition"] == "unconditional"
    changed = copy.deepcopy(rows)
    changed[0]["split"] = "test"
    with pytest.raises(ValueError, match="validation"):
        review.fixed_prompts(recipe, changed)
    with pytest.raises(ValueError, match="Missing"):
        review.fixed_prompts(recipe, rows[1:])
    with pytest.raises(ValueError, match="unique"):
        review.fixed_prompts(recipe, rows + rows[:1])
    changed = copy.deepcopy(rows)
    changed[0]["text"] = "A different story. It has changed."
    with pytest.raises(ValueError, match="changed"):
        review.fixed_prompts(recipe, changed)


def test_review_parent_cannot_skip_sft_or_use_partial_checkpoint():
    plan = {"plan_id": "plan", "config": {"stages": [{"targets": 80}, {"targets": 20}]}}
    run = {"id": "foundation-transformer-s0", "kind": "transformer", "seed": 0}
    ckpt = {
        "identity": {"plan_id": "plan", "run": run, "precision": "float32"},
        "stats": {"stage": 2, "stage_targets": 0, "targets": 100, "updates": 10},
        "complete": True,
    }
    review.check_complete_parent(ckpt, plan, run)
    for field, value in [
        ("stage", 1),
        ("stage_targets", 20),
        ("targets", 80),
        ("updates", 0),
    ]:
        bad = copy.deepcopy(ckpt)
        bad["stats"][field] = value
        with pytest.raises(ValueError, match="complete"):
            review.check_complete_parent(bad, plan, run)
    ckpt["complete"] = False
    with pytest.raises(ValueError, match="complete"):
        review.check_complete_parent(ckpt, plan, run)


def test_review_manifest_binds_decoding_and_source():
    rows, recipe = panel_fixture()
    plan = {
        "plan_id": "plan",
        "corpus_sha256": "corpus",
        "tokenizer_spec": {"sha256": "tok"},
        "config": {"decoding": {"seed": 17}},
    }
    value = {
        "plan_id": "plan",
        "corpus_sha256": "corpus",
        "tokenizer_sha256": "tok",
        "decoding": {"seed": 17},
        "source_sha256": source_sha256(review.__file__),
        "prompts": review.fixed_prompts(recipe, rows),
        "expected_samples": 34,
    }
    value["review_id"] = signature(value)
    review.verify_review(value, plan)
    value["decoding"]["seed"] = 99
    with pytest.raises(ValueError, match="Changed"):
        review.verify_review(value, plan)
    value.pop("review_id")
    value["review_id"] = signature(value)
    with pytest.raises(ValueError, match="match"):
        review.verify_review(value, plan)


def test_review_generation_checks_both_parents_and_keeps_all_samples(
    tmp_path, monkeypatch, codec
):
    from dataclasses import asdict

    torch.set_num_threads(2)
    rows, recipe = panel_fixture()
    plan = {
        "plan_id": "synthetic-unit-fixture",
        "corpus_sha256": "fixture",
        "tokenizer": "fixture",
        "tokenizer_spec": {"sha256": "fixture"},
        "config": {
            "stages": [{"targets": 80}, {"targets": 20}],
            "decoding": {
                "seed": 17,
                "temperature": 0.8,
                "top_k": 4,
                "max_new_tokens": 2,
            },
        },
        "runs": [
            {"id": f"foundation-{k}-s0", "kind": k, "seed": 0}
            for k in ("transformer", "mingru")
        ],
        "models": {},
    }
    for run in plan["runs"]:
        config = FoundationConfig(
            run["kind"],
            vocab_size=259,
            embedding_width=8,
            width=8,
            layers=2,
            heads=2,
            context=256,
        )
        plan["models"][run["kind"]] = {"config": asdict(config)}
        parent = tmp_path / run["id"]
        parent.mkdir()
        torch.save(
            {
                "identity": {
                    "plan_id": plan["plan_id"],
                    "run": run,
                    "precision": "float32",
                },
                "stats": {
                    "stage": 2,
                    "stage_targets": 0,
                    "targets": 100,
                    "updates": 10,
                },
                "complete": run["kind"] == "transformer",
                "model": build_foundation(config).state_dict(),
            },
            parent / "final.pt",
        )
    manifest = {
        "plan_id": plan["plan_id"],
        "corpus_sha256": "fixture",
        "tokenizer_sha256": "fixture",
        "decoding": plan["config"]["decoding"],
        "source_sha256": source_sha256(review.__file__),
        "prompts": review.fixed_prompts(recipe, rows),
        "expected_samples": 34,
    }
    manifest["review_id"] = signature(manifest)
    manifest_path = tmp_path / "manifest.json"
    write_json(manifest_path, manifest)
    monkeypatch.setattr(review, "load_plan", lambda _: plan)
    monkeypatch.setattr(review, "FrozenTokenizer", lambda *_: codec)
    output = tmp_path / "review"
    with pytest.raises(ValueError, match="complete"):
        review.generate_review("fixture", manifest_path, tmp_path, output)
    assert not output.exists()  # First parent must not leak an early panel.
    checkpoint = tmp_path / "foundation-mingru-s0/final.pt"
    saved = torch.load(checkpoint, weights_only=True)
    saved["complete"] = True
    torch.save(saved, checkpoint)
    result = review.generate_review("fixture", manifest_path, tmp_path, output)
    samples = read_rows(output / "samples.jsonl")
    assert result["samples"] == len(samples) == 34
    assert read_json(output / "completed.json")["writing_gate_passed"] is None
    assert all(
        r["human_label"] is None and not r["primary_evaluation"] for r in samples
    )
    assert len({(r["run_id"], r["condition"], r["source_id"]) for r in samples}) == 34
    with pytest.raises(FileExistsError):
        review.generate_review("fixture", manifest_path, tmp_path, output)
