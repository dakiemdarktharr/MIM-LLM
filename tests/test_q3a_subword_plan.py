"""Nonoptimizing safeguards; no real primary plan or writing approval created."""

import copy
from dataclasses import asdict

import pytest
import torch

from mim_llm.foundation.modeling import FoundationConfig
from mim_llm.q3a.io import read_json, sha256, write_json
from mim_llm.q3a_subword import plan, runner
from mim_llm.training_gate import TrainingNotAuthorized


def test_subword_config_preserves_seed_matrix_and_rejects_invalid_objectives():
    c = read_json("configs/q3a/subword_post.template.json")
    plan.validate_config(c)
    for field, value in [
        ("seeds", [0]),
        ("parent_initialization", "same_seed0_parent_for_every_seed"),
        ("learning_rate", float("nan")),
        ("post_targets", 0),
        ("js_weight", -1),
    ]:
        bad = copy.deepcopy(c)
        bad[field] = value
        with pytest.raises(ValueError):
            plan.validate_config(bad)


def test_missing_foundations_do_not_make_a_primary_plan():
    c = read_json("configs/q3a/subword_post.template.json")
    with pytest.raises(ValueError, match="all six"):
        plan.resolve_parents([], c)


def test_real_subword_post_ids_remain_unauthorized_before_loading_a_plan(
    monkeypatch, tmp_path
):
    def forbidden(_):
        raise AssertionError(
            "Permission must fail before reading data or creating a model"
        )

    monkeypatch.setattr(runner, "load_plan", forbidden)
    with pytest.raises(TrainingNotAuthorized):
        runner.execute(
            "not-a-real-plan",
            "subword-post-A1-transformer-s0",
            tmp_path,
            seconds_limit=1,
        )
    assert list(tmp_path.iterdir()) == []


def test_parent_matrix_requires_seed_identity_completion_and_archive_audit(
    tmp_path, monkeypatch
):
    config = read_json("configs/q3a/subword_post.template.json")
    config["context"] = 256
    items, foundations = [], {}
    for kind in config["backbones"]:
        for seed in config["seeds"]:
            name = kind + "-s" + str(seed)
            run = {"id": "foundation-" + name, "kind": kind, "seed": seed}
            foundation_path = tmp_path / (name + "-plan.json")
            checkpoint = tmp_path / (name + ".pt")
            audit = tmp_path / (name + "-audit.json")
            foundation = {
                "plan_id": "synthetic-fixture-" + name,
                "runs": [run],
                "config": {
                    "stages": [
                        {"name": "lm", "targets": 80},
                        {"name": "sft", "targets": 20},
                    ]
                },
                "models": {
                    kind: {
                        "config": asdict(
                            FoundationConfig(
                                kind,
                                width=64 if kind == "transformer" else 325,
                                context=256,
                            )
                        ),
                        "actual_parameters": 1,
                    }
                },
                "tokenizer": "synthetic-snapshot",
                "tokenizer_spec": {"sha256": "synthetic-digest"},
                "corpus_sha256": "synthetic-corpus",
            }
            write_json(foundation_path, foundation)
            torch.save(
                {
                    "identity": {
                        "plan_id": foundation["plan_id"],
                        "run": run,
                        "precision": "float32",
                    },
                    "stats": {
                        "stage": 2,
                        "stage_targets": 0,
                        "targets": 100,
                        "updates": 1,
                    },
                    "complete": True,
                    "model": {"synthetic_tensor_not_trained": torch.tensor([seed])},
                },
                checkpoint,
            )
            write_json(
                audit,
                {
                    "plan_id": foundation["plan_id"],
                    "archive_sha256": "synthetic-unit-archive",
                    "runs": {
                        run["id"]: {
                            "complete": True,
                            "per_stage": {"lm": 80, "sft": 20},
                            "final_sha256": sha256(checkpoint),
                        }
                    },
                },
            )
            items.append(
                {
                    "foundation_plan": str(foundation_path),
                    "run_id": run["id"],
                    "checkpoint": str(checkpoint),
                    "verification_receipt": str(audit),
                }
            )
            foundations[str(foundation_path)] = foundation
    monkeypatch.setattr(plan, "load_foundation_plan", lambda p: foundations[str(p)])
    parents, models, _ = plan.resolve_parents(items, config)
    assert len(parents) == 6 and set(models) == {"mingru", "transformer"}
    assert {p["run"]["seed"] for p in parents.values()} == {0, 1, 2}
    with pytest.raises(ValueError, match="all six"):
        plan.resolve_parents(items[:-1], config)
    with pytest.raises(ValueError, match="Duplicate"):
        plan.resolve_parents(items + items[:1], config)
    first = items[0]
    audit = read_json(first["verification_receipt"])
    audit["runs"][first["run_id"]]["per_stage"]["sft"] = 0
    write_json(first["verification_receipt"], audit, replace=True)
    with pytest.raises(ValueError, match="archive audit"):
        plan.resolve_parents(items, config)


def test_writing_gate_is_bound_to_parents_and_rechecks_underlying_evidence(tmp_path):
    evidence = tmp_path / "synthetic-unit-evidence.txt"
    evidence.write_text(
        "Synthetic fixture only, no real human ratings.", encoding="utf-8"
    )
    parents = {
        k: {"run": {"seed": 0, "id": "foundation-" + k}, "checkpoint_sha256": k}
        for k in ("mingru-s0", "transformer-s0")
    }
    gate = {
        "status": "reviewed_writing_feasibility_passed",
        "decision_reason": "Synthetic unit fixture, not a real approval",
        "foundation_checkpoint_sha256": {"foundation-" + k: k for k in parents},
        "evidence": [{"path": str(evidence), "sha256": sha256(evidence)}],
    }
    path = tmp_path / "fixture-gate.json"
    write_json(path, gate)
    assert plan.checked_writing_gate(path, parents)["sha256"] == sha256(path)
    evidence.write_text("Changed synthetic fixture.", encoding="utf-8")
    with pytest.raises(ValueError, match="Changed writing evidence"):
        plan.checked_writing_gate(path, parents)
