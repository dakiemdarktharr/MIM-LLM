"""Fictional complete panels exercise contracts, never real human/model results.

Fixture checkpoint counters are synthetic metadata; no optimizer is constructed
or stepped. Actual parent/permission gates are covered in the separate plan tests.
"""
# ruff: noqa: F811 -- pytest fixture imported by name.

import copy
import csv
from dataclasses import asdict
from pathlib import Path

import pytest
import torch
from test_foundation import codec  # noqa: F401

from mim_llm.foundation.modeling import FoundationConfig, build_foundation
from mim_llm.q3a.data import make_bundle
from mim_llm.q3a.evaluate import FIELDS, blind_packet
from mim_llm.q3a.io import read_rows, sha256, source_sha256, write_json, write_rows
from mim_llm.q3a_subword import analysis, evaluate


@pytest.fixture
def panel(codec, tmp_path, monkeypatch):
    torch.set_num_threads(2)
    config = {
        "arms": ["A0", "A1", "A2", "A3"],
        "backbones": ["mingru", "transformer"],
        "seeds": [0, 1, 2],
        "gpu_hours_cap_per_study": 1.0,
        "decoding": {
            "seeds": [17],
            "temperature": 0.8,
            "top_k": 40,
            "max_new_tokens": 128,
        },
    }
    runs = [
        {
            "id": f"subword-post-{a}-{k}-s{s}",
            "arm": a,
            "kind": k,
            "seed": s,
            "targets": 7,
            "parent_key": f"{k}-s{s}",
        }
        for k in config["backbones"]
        for s in config["seeds"]
        for a in config["arms"]
    ]
    plan = {
        "plan_id": "SYNTHETIC-not-a-real-plan",
        "dataset_id": "SYNTHETIC-data",
        "runs": runs,
        "config": config,
        "writing_gate": {"synthetic_fixture_only": True},
        "data_dir": str(tmp_path / "data"),
        "tokenizer": str(codec.path),
        "tokenizer_spec": codec.spec,
        "models": {},
        "parents": {
            r["parent_key"]: {
                "checkpoint_sha256": "SYNTHETIC-parent-" + r["parent_key"]
            }
            for r in runs
        },
    }
    for split in ["validation", "test"]:
        write_rows(
            Path(plan["data_dir"]) / (split + ".jsonl"),
            [make_bundle("SYNTHETIC-" + split, split, 123, 0)],
        )
    plan["data_sha256"] = {"test.jsonl": sha256(Path(plan["data_dir"]) / "test.jsonl")}
    paths = []
    for kind in config["backbones"]:
        cfg = FoundationConfig(
            kind,
            vocab_size=259,
            embedding_width=8,
            width=10 if kind == "mingru" else 8,
            layers=2,
            heads=2,
            context=4096,
        )
        model = build_foundation(cfg)
        plan["models"][kind] = {
            "config": asdict(cfg),
            "actual_parameters": sum(p.numel() for p in model.parameters()),
        }
        for run in [r for r in runs if r["kind"] == kind]:
            parent = plan["parents"][run["parent_key"]]["checkpoint_sha256"]
            path = tmp_path / (run["id"] + ".pt")
            torch.save(
                {
                    "run": run,
                    "plan_id": plan["plan_id"],
                    "parent_sha256": parent,
                    "identity": {
                        "plan_id": plan["plan_id"],
                        "run": run,
                        "parent_sha256": parent,
                        "precision": "float32_TF32_disabled",
                        "mha_fastpath_enabled": False,
                    },
                    "stats": {"targets": 7, "updates": 1},
                    "complete": True,
                    "model": model.state_dict(),
                    "config": asdict(cfg),
                    "tokenizer_spec": codec.spec,
                },
                path,
            )
            paths.append(path)
    monkeypatch.setattr(evaluate, "load_plan", lambda p: plan)
    monkeypatch.setattr(analysis, "load_plan", lambda p: plan)

    def synthetic_generation(model, tokenizer, prompt, **kwargs):
        return {
            "prompt": prompt,
            "continuation": "!",
            "token_ids": [0],
            "valid_utf8": True,
            "human_label": None,
            "eos_emitted": True,
            "cap_reached": False,
        }

    monkeypatch.setattr(evaluate, "generate", synthetic_generation)
    reg = {
        "status": "frozen_before_test_generation",
        "plan_id": plan["plan_id"],
        "test_results_used": False,
        "primary_contrast": ["A1", "A2"],
        "primary_metric": analysis.PRIMARY_METRIC,
        "analysis_version": analysis.VERSION,
        "analysis_source_sha256": source_sha256(analysis.__file__),
        "quality_aggregation": analysis.QUALITY_RULE,
        "complete_source_seed_grid_required": True,
        "test_arms": config["arms"],
        "two_independent_readers_planned": True,
        "sample_method_and_rationale": "FICTIONAL UNIT SAMPLE",
        "smallest_useful_effect": 0.1,
        "gpu_hours_cap_per_study": 1.0,
        "test_source_ids": ["SYNTHETIC-test"],
    }
    registration = tmp_path / "SYNTHETIC-registration.json"
    write_json(registration, reg)
    evidence = tmp_path / "SYNTHETIC-validation.txt"
    evidence.write_text("FICTIONAL UNIT EVIDENCE; not scientific review")
    return plan, paths, registration, evidence


def freeze(panel, tmp_path):
    _, paths, registration, evidence = panel
    selection = tmp_path / "selection.json"
    evaluate.freeze_selection(
        "mock-plan",
        paths,
        registration,
        selection,
        rationale="FICTIONAL UNIT CHOICE",
        validation_evidence=[evidence],
    )
    return selection


def test_test_stays_locked_and_incomplete_grid_never_reads_test(
    panel, tmp_path, monkeypatch
):
    _, paths, registration, evidence = panel
    with pytest.raises(ValueError, match="locked"):
        evaluate.generate_panel(
            "mock", paths[0], tmp_path / "never.jsonl", split="test"
        )

    def do_not_read(*args):
        raise AssertionError("Incomplete selection must not parse any test source")

    monkeypatch.setattr(evaluate, "read_rows", do_not_read)
    with pytest.raises(ValueError, match="24"):
        evaluate.freeze_selection(
            "mock",
            paths[:-1],
            registration,
            tmp_path / "locked.json",
            rationale="UNIT",
            validation_evidence=[evidence],
        )


def test_freeze_binds_run_weights_registration_and_evidence(panel, tmp_path):
    plan, paths, _, evidence = panel
    selection = freeze(panel, tmp_path)
    frozen = evaluate.read_selection(plan, selection)
    assert len(frozen["checkpoints"]) == 24 and not frozen["test_performance_measured"]
    original_backend = torch.backends.mha.get_fastpath_enabled()
    result = evaluate.generate_panel(
        "mock", paths[0], tmp_path / "out.jsonl", split="test", selection=selection
    )
    rows = read_rows(tmp_path / "out.jsonl")
    assert torch.backends.mha.get_fastpath_enabled() == original_backend
    assert result["complete"] and result["generations"] == 3
    assert {r["role"] for r in rows} == {"base", "effective", "noop"}
    assert all(r["token_ids"] == [0] and r["human_label"] is None for r in rows)
    evidence.write_text("changed fixture")
    with pytest.raises(ValueError, match="evidence changed"):
        evaluate.generate_panel(
            "mock",
            paths[1],
            tmp_path / "never2.jsonl",
            split="test",
            selection=selection,
        )


def test_checkpoint_cannot_be_partial_or_from_a_different_parent(panel, tmp_path):
    plan, paths, _, _ = panel
    saved = torch.load(paths[0], weights_only=True)
    for field, value in [("complete", False), ("parent_sha256", "other")]:
        bad = copy.deepcopy(saved)
        bad[field] = value
        path = tmp_path / (field + ".pt")
        torch.save(bad, path)
        with pytest.raises(ValueError, match="complete declared"):
            evaluate.complete_checkpoint(path, plan)


def test_primary_only_annotation_sample_still_freezes_all_24_runs(panel, tmp_path):
    from mim_llm.q3a.io import read_json

    _, paths, registration, _ = panel
    reg = read_json(registration)
    reg["test_arms"] = ["A1", "A2"]
    write_json(registration, reg, replace=True)
    selection = freeze(panel, tmp_path)
    with pytest.raises(ValueError, match="registered test-arm"):
        evaluate.generate_panel(
            "mock",
            paths[0],
            tmp_path / "never.jsonl",
            split="test",
            selection=selection,
        )
    result = evaluate.generate_panel(
        "mock", paths[1], tmp_path / "primary.jsonl", split="test", selection=selection
    )
    assert result["run"]["arm"] == "A1" and result["generations"] == 3


def test_partial_generation_is_retained_without_completion_receipt(
    panel, tmp_path, monkeypatch
):
    _, paths, _, _ = panel
    original = evaluate.generate
    counter = 0

    def interrupted(*args, **kwargs):
        nonlocal counter
        counter += 1
        if counter == 2:
            raise RuntimeError("SYNTHETIC INTERRUPTION")
        return original(*args, **kwargs)

    monkeypatch.setattr(evaluate, "generate", interrupted)
    output = tmp_path / "partial.jsonl"
    original_backend = torch.backends.mha.get_fastpath_enabled()
    with pytest.raises(RuntimeError, match="INTERRUPTION"):
        evaluate.generate_panel("mock", paths[0], output)
    assert len(read_rows(output)) == 1
    assert Path(str(output) + ".started.json").is_file()
    assert not Path(str(output) + ".receipt.json").exists()
    assert torch.backends.mha.get_fastpath_enabled() == original_backend
    with pytest.raises(FileExistsError):
        evaluate.generate_panel("mock", paths[0], output)


def test_subword_join_accepts_token_zero_and_detects_repaired_text(panel, tmp_path):
    plan, paths, _, _ = panel
    output = tmp_path / "gen.jsonl"
    evaluate.generate_panel("mock", paths[0], output)
    packet = tmp_path / "packet"
    blind_packet([output], packet)
    key = read_rows(packet / "PRIVATE-key.jsonl")
    _, valid = analysis.join_generations(plan, key, [output])
    assert all(valid.values())
    rows = read_rows(output)
    rows[0]["continuation"] = "repaired"
    output.unlink()
    write_rows(output, rows)
    write_json(
        str(output) + ".receipt.json",
        {"complete": True, "output_sha256": sha256(output)},
        replace=True,
    )
    with pytest.raises(ValueError, match="unmodified subword"):
        analysis.join_generations(plan, key, [output])


def test_synthetic_two_reader_analysis_preserves_primary_and_averages_quality(
    panel, tmp_path
):
    _, paths, _, _ = panel
    files = []
    for i, path in enumerate(paths):
        output = tmp_path / f"synthetic-panel-{i}.jsonl"
        evaluate.generate_panel("mock", path, output)
        files.append(output)
    packet = tmp_path / "packet"
    packet_result = evaluate.prepare_blind_packet("mock", files, packet)
    assert packet_result["actual_human_labels"] == 0
    key = read_rows(packet / "PRIVATE-key.jsonl")
    labels = []
    for index in [0, 1]:
        path = tmp_path / f"SYNTHETIC-reader-{index}.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            for item in key:
                row = {name: 0 for name in FIELDS}
                row.update(
                    item_id=item["item_id"],
                    rater_id=f"FICTIONAL-UNIT-{index}",
                    contradiction_type="none",
                    coverage_fraction=0.25 + index * 0.5,
                    fluency_1_to_5=1 + index * 4,
                    evidence="SYNTHETIC UNIT LABEL; not a real human rating",
                )
                writer.writerow(row)
        labels.append(path)
    result = analysis.reviewed_analyze(
        "mock", *labels, packet / "PRIVATE-key.jsonl", files, draws=100
    )
    assert result["all_three_training_seeds_present"]
    assert all(r["effect"] == 0 for r in result["primary_results"])
    assert all(
        r["coverage"] == 0.5 and r["fluency"] == 3 for r in result["quality_summaries"]
    )
    assert result["analysis_provenance"]["primary_definition_changed"] is False
