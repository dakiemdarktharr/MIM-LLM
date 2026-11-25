"""Deferred optimizer tests. Real training permission is required by conftest.

Artificial bank fixtures test engine resume only, not scientific provenance or
model-generated-history quality. None of these tests runs under the current hold.
"""

import importlib
from dataclasses import asdict, replace

import pytest
import torch

from mim_llm.models import build_model, parameter_count
from mim_llm.q3a.data import prepare as prepare_a
from mim_llm.q3a.io import read_json, sha256, signature, write_json, write_rows
from mim_llm.q3a.runner import execute as execute_a
from mim_llm.q3bc.data import prepare
from mim_llm.q3bc.objectives import examples_for


@pytest.mark.training
@pytest.mark.parametrize("study", ["b", "c"])
@pytest.mark.parametrize("kind", ["mingru", "transformer"])
def test_bc_optimizer_and_interrupted_resume(tmp_path, monkeypatch, study, kind):
    ap = importlib.import_module("mim_llm.q3a.plan")
    bp = importlib.import_module("mim_llm.q3bc.plan")
    runner = importlib.import_module("mim_llm.q3bc.runner")
    gate = importlib.import_module("mim_llm.training_gate")
    a_data = tmp_path / "a-data"
    prepare_a(a_data, train_sources=3, validation_sources=1, test_sources=1)
    warm = tmp_path / "warm.jsonl"
    write_rows(
        warm,
        [
            {"source_id": "unit-" + s, "split": s, "text": "FICTIONAL UNIT " + s}
            for s in ("train", "validation", "test")
        ],
    )
    write_json(
        str(warm) + ".manifest.json",
        {"license": "UNIT", "revision": "unit-pin", "sha256": sha256(warm)},
    )
    ca = read_json("configs/q3a/pilot.json")
    ca.update(
        warmup_targets=64, post_targets=2000, batch_size=1, checkpoint_every_updates=1
    )
    ac = tmp_path / "a.json"
    write_json(ac, ca)

    def tiny_match(target, template):
        c = replace(template, width=8)
        return {
            "config": asdict(c),
            "actual_parameters": parameter_count(build_model(c)),
            "relative_parameter_gap": 0.0,
        }

    monkeypatch.setattr(ap, "match_width", tiny_match)
    shared_path = tmp_path / "shared.json"
    shared = ap.make_plan(ac, a_data, warm, shared_path)
    data = tmp_path / "study-data"
    prepare(study, data, train_sources=3, validation_sources=1, test_sources=1)
    config = read_json(f"configs/q3{study}/pilot.json")
    config.update(post_targets=2000, batch_size=1, checkpoint_every_updates=1)
    if study == "c":
        config["minimum_matched_sources"] = 1
    config_path = tmp_path / "study.json"
    write_json(config_path, config)
    base_path = tmp_path / "base.json"
    plan = bp.make_plan(study, config_path, data, shared_path, base_path)
    parent = f"warmup-{kind}-s0"
    run = f"{study.upper()}2-{kind}-s0"
    initial = tmp_path / "initial"
    permission = tmp_path / "UNIT-permission.json"
    write_json(
        permission,
        {
            "model_training_authorized": True,
            "tokenizer_fitting_authorized": False,
            "authorized_run_ids": [parent, run],
            "authorized_plan_ids": [shared["plan_id"], plan["plan_id"]],
        },
    )
    monkeypatch.setattr(gate, "POLICY", permission)
    execute_a(shared_path, parent, initial, seconds_limit=120)
    path = base_path
    if study == "c":
        bank = tmp_path / "UNIT-sealed"
        bank.mkdir()
        hashes = {}
        parent_sha = sha256(initial / parent / "final.pt")
        fixtures = examples_for(plan, plan["runs"][0], contract_fixture=True)
        for r in plan["runs"]:
            rows = [
                {k: v for k, v in x.items() if k != "contract_fixture"}
                | {"frozen_learner_sha256": parent_sha}
                for x in fixtures
            ]
            f = bank / (r["id"] + ".jsonl")
            write_rows(f, rows)
            hashes[f.name] = sha256(f)
        m = {
            "ready": True,
            "shared_plan_id": shared["plan_id"],
            "dataset_id": plan["dataset_id"],
            "raw_bank_id": "UNIT-ARTIFICIAL",
            "sha256": hashes,
            "minimum_sources": 1,
            "max_nll_gap": 0.25,
            "max_length_gap": 32,
        }
        m["sealed_bank_id"] = signature(m)
        write_json(bank / "manifest.json", m)
        path = tmp_path / "bound.json"
        plan = bp.bind_bank(base_path, bank, path)
        policy = read_json(permission)
        policy["authorized_plan_ids"].append(plan["plan_id"])
        write_json(permission, policy, replace=True)
    full = tmp_path / "full"
    resumed = tmp_path / "resumed"
    expected = runner.execute(path, run, full, warmup_root=initial, seconds_limit=120)
    original = runner.atomic_checkpoint
    stopped = False

    def interrupt(p, value):
        nonlocal stopped
        original(p, value)
        if not stopped and p.name == "latest.pt" and value["stats"]["updates"] == 1:
            stopped = True
            raise RuntimeError("UNIT simulated interruption")

    monkeypatch.setattr(runner, "atomic_checkpoint", interrupt)
    with pytest.raises(RuntimeError, match="simulated"):
        runner.execute(path, run, resumed, warmup_root=initial, seconds_limit=120)
    monkeypatch.setattr(runner, "atomic_checkpoint", original)
    actual = runner.execute(
        path, run, resumed, warmup_root=initial, seconds_limit=120, resume=True
    )
    assert (
        actual["complete"]
        and expected["complete"]
        and actual["stats"]["trained_targets"] == 2000
    )
    a = torch.load(full / run / "final.pt", weights_only=True)["model"]
    b = torch.load(resumed / run / "final.pt", weights_only=True)["model"]
    for key in a:
        torch.testing.assert_close(a[key], b[key], rtol=0, atol=0)
