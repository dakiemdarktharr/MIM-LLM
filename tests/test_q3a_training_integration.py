"""Explicitly deferred optimizer tests: never run under the current training hold.

The autouse fixture checks real user authorization before this module's test
body can use a temporary, test-only permission policy.
"""

import importlib
import shutil
from dataclasses import asdict, replace

import pytest
import torch

from mim_llm.models import build_model, parameter_count
from mim_llm.q3a.data import prepare
from mim_llm.q3a.io import read_json, sha256, write_json, write_rows
from mim_llm.q3a.runner import execute


@pytest.mark.training
@pytest.mark.parametrize("kind", ["mingru", "transformer"])
def test_q3a_optimizer_js_and_interruption_resume(tmp_path, monkeypatch, kind):
    planning = importlib.import_module("mim_llm.q3a.plan")
    runner = importlib.import_module("mim_llm.q3a.runner")
    gate = importlib.import_module("mim_llm.training_gate")
    data = tmp_path / "data"
    prepare(data, train_sources=3, validation_sources=1, test_sources=1)
    warmup = tmp_path / "warmup.jsonl"
    write_rows(
        warmup,
        [
            {"source_id": "unit-" + s, "split": s, "text": "FICTIONAL UNIT " + s}
            for s in ("train", "validation", "test")
        ],
    )
    write_json(
        str(warmup) + ".manifest.json",
        {"license": "UNIT-ONLY", "revision": "unit-pin", "sha256": sha256(warmup)},
    )
    config = read_json("configs/q3a/pilot.json")
    config.update(
        warmup_targets=64, post_targets=300, batch_size=1, checkpoint_every_updates=1
    )
    config_path = tmp_path / "config.json"
    write_json(config_path, config)

    def match(target, template):
        cfg = replace(template, width=8)
        return {
            "config": asdict(cfg),
            "actual_parameters": parameter_count(build_model(cfg)),
            "relative_parameter_gap": 0.0,
        }

    monkeypatch.setattr(planning, "match_width", match)
    plan_path = tmp_path / "plan.json"
    plan = planning.make_plan(config_path, data, warmup, plan_path)
    parent = f"warmup-{kind}-s0"
    run = f"A3-{kind}-s0"
    policy = tmp_path / "TEST-ONLY-permission.json"
    write_json(
        policy,
        {
            "model_training_authorized": True,
            "tokenizer_fitting_authorized": False,
            "authorized_run_ids": [parent, run],
            "authorized_plan_ids": [plan["plan_id"]],
        },
    )
    monkeypatch.setattr(gate, "POLICY", policy)
    full = tmp_path / "full"
    resumed = tmp_path / "resumed"
    execute(plan_path, parent, full, seconds_limit=60)
    shutil.copytree(full / parent, resumed / parent)
    expected = execute(plan_path, run, full, seconds_limit=60)
    original = runner.atomic_checkpoint
    interrupted = False

    def interrupt(path, value):
        nonlocal interrupted
        original(path, value)
        if (
            not interrupted
            and path.name == "latest.pt"
            and value["stats"]["updates"] == 1
        ):
            interrupted = True
            raise RuntimeError(
                "UNIT simulated interruption after a complete checkpoint"
            )

    monkeypatch.setattr(runner, "atomic_checkpoint", interrupt)
    with pytest.raises(RuntimeError, match="simulated interruption"):
        execute(plan_path, run, resumed, seconds_limit=60)
    monkeypatch.setattr(runner, "atomic_checkpoint", original)
    actual = execute(plan_path, run, resumed, seconds_limit=60, resume=True)
    assert actual["complete"] and expected["complete"]
    assert (
        actual["stats"]["trained_targets"]
        == expected["stats"]["trained_targets"]
        == 300
    )
    assert actual["stats"]["probe_positions"] > 0
    a = torch.load(full / run / "final.pt", weights_only=True)["model"]
    b = torch.load(resumed / run / "final.pt", weights_only=True)["model"]
    for name in a:
        torch.testing.assert_close(a[name], b[name], rtol=0, atol=0)
