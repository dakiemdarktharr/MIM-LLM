"""Authorized CPU optimizer checks on static synthetic fixtures, not paper runs."""
# ruff: noqa: F811 -- pytest resolves the imported fixture by argument name.

import copy
import json
from dataclasses import asdict

import pytest
import torch
from test_foundation import codec  # noqa: F401
from test_q3a_subword import bundle

from mim_llm import training_gate
from mim_llm.foundation.modeling import FoundationConfig, build_foundation
from mim_llm.q3a.io import read_rows, sha256, write_rows
from mim_llm.q3a_subword import runner


@pytest.mark.training
@pytest.mark.parametrize("kind", ["mingru", "transformer"])
def test_subword_post_optimizer_and_exact_resume(codec, tmp_path, monkeypatch, kind):
    torch.set_num_threads(2)
    cfg = FoundationConfig(
        kind,
        vocab_size=259,
        embedding_width=8,
        width=10 if kind == "mingru" else 8,
        layers=2,
        heads=2,
        context=256,
    )
    torch.manual_seed(321)
    model = build_foundation(cfg)
    parent_run = {"id": f"foundation-{kind}-s0", "kind": kind, "seed": 0}
    foundation = {
        "plan_id": "synthetic-foundation-fixture",
        "config": {"stages": [{"targets": 80}, {"targets": 20}]},
    }
    parent_path = tmp_path / "synthetic-parent.pt"
    torch.save(
        {
            "identity": {
                "plan_id": foundation["plan_id"],
                "run": parent_run,
                "precision": "float32",
            },
            "stats": {"stage": 2, "stage_targets": 0, "targets": 100, "updates": 1},
            "complete": True,
            "model": model.state_dict(),
        },
        parent_path,
    )
    b = bundle()
    b["source_id"] = "synthetic-train"
    b["scenarios"]["effective"] = copy.deepcopy(b["scenarios"]["base"])
    b["scenarios"]["surface"] = copy.deepcopy(b["scenarios"]["base"])
    b["scenarios"]["effective"]["world"]["power_return"] = 6
    for s in b["scenarios"].values():
        s["prompt"] += "Story:\n"
        s["reference"] = "Mai kept it."
    valid = copy.deepcopy(b)
    valid["source_id"] = "synthetic-validation"
    data = tmp_path / "data"
    write_rows(data / "train.jsonl", [b])
    write_rows(data / "validation.jsonl", [valid])
    run_id = f"subword-post-A3-{kind}-s0"
    run = {
        "id": run_id,
        "arm": "A3",
        "kind": kind,
        "seed": 0,
        "targets": 77,
        "parent_key": kind + "-s0",
    }
    plan = {
        "plan_id": "synthetic-post-fixture",
        "writing_gate": {"fixture": True},
        "config": {
            "context": 256,
            "batch_size": 2,
            "learning_rate": 0.01,
            "weight_decay": 0.01,
            "grad_clip": 1.0,
            "js_weight": 0.1,
            "checkpoint_every_updates": 1,
            "validation_every_updates": 2,
            "gpu_hours_cap_per_study": 0.1,
        },
        "runs": [run],
        "data_dir": str(data),
        "tokenizer": str(codec.path),
        "tokenizer_spec": codec.spec,
        "models": {
            kind: {
                "config": asdict(cfg),
                "actual_parameters": sum(p.numel() for p in model.parameters()),
            }
        },
        "parents": {
            kind + "-s0": {
                "foundation_plan": "fixture-only",
                "run": parent_run,
                "checkpoint": str(parent_path),
                "checkpoint_sha256": sha256(parent_path),
            }
        },
    }
    policy = tmp_path / "isolated-synthetic-permission.json"
    policy.write_text(
        json.dumps(
            {
                "model_training_authorized": True,
                "tokenizer_fitting_authorized": False,
                "authorized_run_ids": [run_id],
                "authorized_plan_ids": [plan["plan_id"]],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(training_gate, "POLICY", policy)
    monkeypatch.setattr(runner, "load_plan", lambda _: plan)
    monkeypatch.setattr(runner, "load_foundation_plan", lambda _: foundation)
    # The synthetic loader isolates optimizer mechanics. Real plan/data/provenance
    # validation is tested separately; this fixture is never a real parent receipt.
    full = runner.execute("fixture", run_id, tmp_path / "full", seconds_limit=30)
    partial = runner.execute(
        "fixture", run_id, tmp_path / "resumed", seconds_limit=30, max_updates=1
    )
    assert not partial["complete"] and partial["stats"]["targets"] < 77
    resumed = runner.execute(
        "fixture", run_id, tmp_path / "resumed", seconds_limit=30, resume=True
    )
    assert full["complete"] and resumed["complete"]
    a = torch.load(tmp_path / "full" / run_id / "final.pt", weights_only=True)
    z = torch.load(tmp_path / "resumed" / run_id / "final.pt", weights_only=True)
    for key in a["model"]:
        torch.testing.assert_close(a["model"][key], z["model"][key], rtol=0, atol=0)
    for key in (
        "targets",
        "input_tokens",
        "probe_input_tokens",
        "probe_positions",
        "updates",
        "epoch",
        "cursor",
    ):
        assert a["stats"][key] == z["stats"][key]
    assert a["stats"]["targets"] == 77 and a["stats"]["probe_positions"] > 0
    assert any(
        not torch.equal(a["model"][k], model.state_dict()[k]) for k in a["model"]
    )
    for state in a["optimizer"]["state"]:
        for key in a["optimizer"]["state"][state]:
            torch.testing.assert_close(
                a["optimizer"]["state"][state][key],
                z["optimizer"]["state"][state][key],
                rtol=0,
                atol=0,
            )
    rows = read_rows(tmp_path / "resumed" / run_id / "metrics.jsonl")
    assert [r["update"] for r in rows] == list(range(1, len(rows) + 1))
    assert sum(r["batch_targets"] for r in rows) == 77
    assert all(r["probe_positions"] > 0 and r["js"] >= -1e-6 for r in rows)
