"""Synthetic unit fixtures only: no training and no claimed human annotations."""

import csv
import math

import pytest
import torch

from mim_llm.models import ModelConfig, build_model
from mim_llm.q3a.data import (
    arm_examples,
    make_bundle,
    prepare,
    state,
    validate_bundle,
    verify_dataset,
)
from mim_llm.q3a.evaluate import (
    analyze,
    blind_packet,
    check_test_release,
    paired_bootstrap,
    read_labels,
)
from mim_llm.q3a.io import read_rows, write_json, write_rows
from mim_llm.q3a.objectives import (
    batch_examples,
    encode_example,
    js_divergence,
    probe_js,
)
from mim_llm.q3a.runner import (
    atomic_checkpoint,
    execute,
    language_examples,
    restore_checkpoint,
    take_batch,
)
from mim_llm.tokenizer import ByteTokenizer
from mim_llm.training_gate import TrainingNotAuthorized, require_training_permission


def test_all_training_entrypoints_locked_before_side_effects(tmp_path, monkeypatch):
    import mim_llm.training_gate as gate
    from mim_llm.tokenizer_train import train_tokenizer
    from mim_llm.train import train

    policy = tmp_path / "closed-policy.json"
    write_json(policy, {"model_training_authorized": False, "tokenizer_fitting_authorized": False})
    monkeypatch.setattr(gate, "POLICY", policy)

    for operation in ("model", "tokenizer"):
        with pytest.raises(TrainingNotAuthorized):
            require_training_permission(operation, "not-authorized")
    with pytest.raises(TrainingNotAuthorized):
        execute("missing", "A1-mingru-s0", tmp_path / "run", seconds_limit=1)
    with pytest.raises(TrainingNotAuthorized):
        train("missing", tmp_path / "old", ModelConfig())
    with pytest.raises(TrainingNotAuthorized):
        train_tokenizer("missing", str(tmp_path / "token.model"))
    assert list(tmp_path.iterdir()) == [policy]


@pytest.mark.parametrize("i", range(20))
def test_counterfactual_contract(i):
    b = make_bundle(f"train-{i}", "train", 2026, i)
    validate_bundle(b)
    base = b["scenarios"]["base"]
    effective = b["scenarios"]["effective"]
    noop = b["scenarios"]["noop"]
    assert base["facts"] == noop["facts"]
    assert base["facts"]["action"] != effective["facts"]["action"]
    assert base["facts"] == b["scenarios"]["surface"]["facts"]
    assert base["prompt"] != b["scenarios"]["surface"]["prompt"]
    assert (
        len(base["prompt"])
        == len(noop["prompt"])
        == len(b["scenarios"]["surface"]["prompt"])
    )
    assert (
        sum(x != y for x, y in zip(base["prompt"], noop["prompt"]))
        == b["scenarios"]["surface"]["character_edits"]
    )
    control = b["scenarios"]["surface"]
    assert base["world"]["background_clock"] != control["world"]["background_clock"]
    assert base["world"]["power_return"] == control["world"]["power_return"]
    assert (
        sum(x != y for x, y in zip(base["prompt"], control["prompt"]))
        == control["character_edits"]
    )
    assert all(len(s["reference"].split(". ")) == 3 for s in b["scenarios"].values())


def test_deadline_inclusive_and_permission_and_overwrites():
    w = {
        "initial_holder": "Lan",
        "transfers": ["Mai", "Huy", "Mai"],
        "deadline": 540,
        "power_return": 540,
        "permission": True,
    }
    assert state(w) == {
        "holder": "Mai",
        "power_available": True,
        "permission": True,
        "action": "open",
        "cabinet": "open",
    }
    assert state({**w, "power_return": 541})["action"] == "wait"
    assert state({**w, "permission": False})["action"] == "wait"


def test_source_disjoint_integrity_and_no_overwrite(tmp_path):
    d = tmp_path / "data"
    m = prepare(d, train_sources=12, validation_sources=3, test_sources=3)
    assert verify_dataset(d) == m
    with pytest.raises(FileExistsError):
        prepare(d)
    with (d / "test.jsonl").open("a") as f:
        f.write("\n")
    with pytest.raises(ValueError, match="Changed split"):
        verify_dataset(d)


def test_arm_exposure_matches_and_a3_data_identical():
    bundles = [make_bundle("a", "train", 8, 0), make_bundle("b", "train", 8, 1)]
    examples = {arm: arm_examples(bundles, arm) for arm in ("A0", "A1", "A2", "A3")}
    assert {len(x) for x in examples.values()} == {8}
    assert examples["A1"] == examples["A3"]
    for rows in examples.values():
        assert sum(r["source_id"] == "a" for r in rows) == 4


def test_shift_response_mask_and_eos_and_padding():
    t = ByteTokenizer()
    row = encode_example("abc", "XY", 64)
    assert row["input_ids"] == t.encode("abcXY", bos=True)
    assert row["targets"] == [-100] * 3 + t.encode("XY", eos=True)
    batch = batch_examples(
        [{"prompt": "abc", "reference": "XY"}, {"prompt": "a", "reference": "Z"}], 64
    )
    assert batch["targets"][1, -1] == -100 and not batch["attention_mask"][1, -1]
    with pytest.raises(ValueError, match="No truncation"):
        encode_example("a" * 65, "b", 64)


@pytest.mark.parametrize("remaining", [1, 2, 3, 4, 5, 6, 20])
def test_exact_target_cap(remaining):
    batch = batch_examples(
        [{"prompt": "p", "reference": "XYZ"}, {"prompt": "q", "reference": "HIJ"}],
        64,
        remaining=remaining,
    )
    assert (batch["targets"] != -100).sum() == min(remaining, 8)


def test_js_symmetric_bounded_and_has_gradients():
    a = torch.randn(4, 259, requires_grad=True)
    b = torch.randn(4, 259, requires_grad=True)
    js = js_divergence(a, b)
    torch.testing.assert_close(js, js_divergence(b, a))
    assert 0 <= float(js.detach()) <= math.log(2) + 1e-6
    assert abs(float(js_divergence(a, a).detach())) < 1e-6
    js.backward()
    assert torch.isfinite(a.grad).all() and torch.isfinite(b.grad).all()


@pytest.mark.parametrize(
    "key", ["holder", "action", "cabinet", "power_available", "permission"]
)
def test_probe_span_loss_never_updates_parameters(key):
    b = make_bundle("a", "train", 8, 1)
    model = build_model(ModelConfig(kind="mingru", width=8, layers=2, context=2048))
    before = {n: p.detach().clone() for n, p in model.named_parameters()}
    loss, cost = probe_js(model, b, 2048, "cpu", probe_key=key)
    loss.backward()
    assert cost["probe_input_tokens"] > cost["probe_positions"] > 0
    assert all(torch.equal(p, before[n]) for n, p in model.named_parameters())


def test_resumable_data_cursor_and_warmup_no_story_crossing():
    x = list(range(7))
    first, e, c = take_batch(x, 4, 0, 0, 5)
    second, e, c = take_batch(x, 4, e, c, 7)
    whole, e2, c2 = take_batch(x, 4, 0, 0, 12)
    assert first + second == whole and (e, c) == (e2, c2)
    rows = language_examples(
        [
            {"source_id": "a", "split": "train", "text": "ABCDEF"},
            {"source_id": "b", "split": "train", "text": "XYZ"},
        ],
        "train",
        3,
    )
    assert len(rows) == 5 and all(len(r["input_ids"]) <= 3 for r in rows)
    assert sum(len(r["targets"]) for r in rows) == 11


def test_checkpoint_roundtrip_without_optimizer_step(tmp_path):
    a = build_model(ModelConfig(kind="mingru", width=8, layers=2))
    oa = torch.optim.AdamW(a.parameters())
    path = tmp_path / "snapshot.pt"
    identity = {"plan": "unit-fixture"}
    atomic_checkpoint(
        path,
        {
            "identity": identity,
            "model": a.state_dict(),
            "optimizer": oa.state_dict(),
            "rng_cpu": torch.get_rng_state(),
            "rng_cuda": None,
        },
    )
    b = build_model(ModelConfig(kind="mingru", width=8, layers=2))
    ob = torch.optim.AdamW(b.parameters())
    restore_checkpoint(path, b, ob, expected=identity)
    for k, v in a.state_dict().items():
        assert torch.equal(v, b.state_dict()[k])
    with pytest.raises(ValueError):
        restore_checkpoint(path, b, ob, expected={"plan": "different"})


def fixture_generations():
    # Deliberately fictional records used only in a temporary unit-test directory.
    rows = []
    for arm in ("A1", "A2"):
        for source in ("unit-source-a", "unit-source-b"):
            for role in ("base", "effective", "noop"):
                rows.append(
                    {
                        "generation_id": f"{arm}/{source}/{role}",
                        "source_id": source,
                        "scenario_id": f"{source}/{role}",
                        "role": role,
                        "split": "validation",
                        "prompt": "UNIT FIXTURE",
                        "continuation": "UNIT FIXTURE",
                        "expected_facts": {},
                        "mandatory": {},
                        "world": {"deadline": 540},
                        "run": {"kind": "mingru", "arm": arm, "seed": 0},
                        "decode_seed": 17,
                        "pairs": [
                            {
                                "kind": "effective",
                                "changed": ["action", "cabinet"],
                                "preserved": ["holder"],
                            },
                            {
                                "kind": "noop",
                                "changed": [],
                                "preserved": ["holder", "action", "cabinet"],
                            },
                        ],
                        "plan_id": "unit-fixture",
                    }
                )
    return rows


def test_blank_packet_is_not_fabricated_labels_and_pair_cluster_analysis(tmp_path):
    path = tmp_path / "unit-generations.jsonl"
    write_rows(path, fixture_generations())
    out = tmp_path / "packet"
    blind_packet([path], out)
    key = read_rows(out / "PRIVATE-key.jsonl")
    ids = {r["item_id"] for r in key}
    with pytest.raises(ValueError, match="rater"):
        read_labels(out / "reader-a.csv", ids)
    byid = {r["item_id"]: r for r in key}
    for name in ("reader-a", "reader-b"):
        file = out / f"{name}.csv"
        with file.open(newline="") as f:
            labels = list(csv.DictReader(f))
        for r in labels:
            r.update(
                rater_id="UNIT-" + name,
                all_mandatory_correct="1"
                if byid[r["item_id"]]["run"]["arm"] == "A1"
                else "0",
                contradiction="0",
                contradiction_type="none",
                format_3_to_5="1",
                coverage_fraction="1",
                fluency_1_to_5="3",
                unclear="0",
                evidence="FICTIONAL UNIT TEST",
            )
            for field in ("holder", "action", "cabinet", "reason"):
                r[field + "_correct"] = r["all_mandatory_correct"]
        with file.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(labels[0]))
            w.writeheader()
            w.writerows(labels)
    result = analyze(
        out / "reader-a.csv", out / "reader-b.csv", out / "PRIVATE-key.jsonl", draws=100
    )
    assert result["primary_results"][0]["effect"] == 1
    assert result["primary_results"][0]["source_clusters"] == 2
    assert result["primary_results"][0]["ci95"] == [1, 1]
    packet = read_rows(out / "packet.jsonl")
    assert all(
        "run" not in r and "arm" not in r and "source_id" not in r for r in packet
    )


def test_bootstrap_keeps_source_unit():
    assert paired_bootstrap([0.5, 0.5], draws=100)["ci95"] == [0.5, 0.5]
    with pytest.raises(ValueError):
        paired_bootstrap([], draws=100)


def test_test_generation_stays_locked():
    with pytest.raises(ValueError, match="locked"):
        check_test_release({}, "missing", None)


def test_plan_hash_budget_and_input_checks_without_training(tmp_path, monkeypatch):
    import importlib
    from dataclasses import asdict, replace

    from mim_llm.models import parameter_count
    from mim_llm.q3a.io import read_json, sha256, write_json

    planning = importlib.import_module("mim_llm.q3a.plan")
    data = tmp_path / "controlled"
    prepare(data, train_sources=3, validation_sources=1, test_sources=1)
    warmup = tmp_path / "warmup.jsonl"
    write_rows(
        warmup,
        [
            {"source_id": "unit-" + s, "split": s, "text": "UNIT FICTIONAL " + s}
            for s in ("train", "validation", "test")
        ],
    )
    write_json(
        str(warmup) + ".manifest.json",
        {"license": "UNIT-TEST-ONLY", "revision": "unit-pin", "sha256": sha256(warmup)},
    )

    def small_match(target, template):
        cfg = replace(template, width=8)
        return {
            "config": asdict(cfg),
            "actual_parameters": parameter_count(build_model(cfg)),
            "relative_parameter_gap": 0.0,
        }

    monkeypatch.setattr(planning, "match_width", small_match)
    output = tmp_path / "plan.json"
    plan = planning.make_plan("configs/q3a/pilot.json", data, warmup, output)
    assert len(plan["runs"]) == 30 and plan["budget"]["post_targets"] == 48_000_000
    assert planning.load_plan(output) == plan
    with pytest.raises(ValueError):
        planning.freeze_selection(
            output, [], tmp_path / "selection.json", rationale="UNIT"
        )
    # Metadata-only FICTIONAL fixtures, never trained checkpoints/results.
    paths = []
    for run in plan["runs"]:
        if run["phase"] != "post":
            continue
        path = tmp_path / (run["id"] + ".pt")
        torch.save({"plan_id": plan["plan_id"], "complete": True, "run": run}, path)
        paths.append(path)
    registration = tmp_path / "registration.json"
    sample = read_rows(data / "test.jsonl")[0]["source_id"]
    write_json(
        registration,
        {
            "plan_id": plan["plan_id"],
            "primary_contrast": ["A1", "A2"],
            "test_results_used": False,
            "smallest_useful_effect": 0.1,
            "gpu_hours_cap_per_study": 1,
            "test_source_ids": [sample],
            "sample_method_and_rationale": "FICTIONAL UNIT TEST",
        },
    )
    selection = tmp_path / "selection.json"
    planning.freeze_selection(
        output, paths, selection, rationale="UNIT ONLY", registration=registration
    )
    assert read_json(selection)["analysis_registration"]["test_source_ids"] == [sample]
    changed = read_json(output)
    changed["config"]["learning_rate"] = 1.0
    write_json(output, changed, replace=True)
    with pytest.raises(ValueError, match="Plan hash"):
        planning.load_plan(output)


def test_generation_suppresses_pad_and_bos():
    from torch import nn

    from mim_llm.generate import generate_from_ids

    class Dummy(nn.Module):
        def forward(self, ids, *, return_state=False, state=None):
            logits = torch.zeros(ids.shape[0], ids.shape[1], 259)
            logits[:, :, 0] = 100
            logits[:, :, 1] = 99
            logits[:, :, 68] = 98
            return logits, None, {}

    sample = generate_from_ids(
        Dummy(), ByteTokenizer(), [1, 68], max_new_tokens=3, top_k=1
    )
    assert sample["token_ids"] == [68, 68, 68]


@pytest.mark.parametrize("device", ["cpu", "cuda"])
def test_transformer_kv_cache_matches_full_chunks_and_padding(device):
    if device == "cuda" and not torch.cuda.is_available():
        pytest.skip("CUDA unavailable")
    model = (
        build_model(
            ModelConfig(
                kind="transformer", width=24, layers=2, context=128, dropout=0.2
            )
        )
        .to(device)
        .eval()
    )
    ids = torch.tensor([[1, 4, 5, 6, 7, 8, 9], [1, 11, 12, 13, 0, 0, 0]], device=device)
    mask = ids != 0
    with torch.no_grad():
        full, _ = model(ids, mask)
        a, _, s = model(ids[:, :3], mask[:, :3], return_state=True)
        b, _, s = model(ids[:, 3:5], mask[:, 3:5], state=s, return_state=True)
        c, _, s = model(ids[:, 5:], mask[:, 5:], state=s, return_state=True)
    torch.testing.assert_close(full, torch.cat((a, b, c), 1), rtol=2e-5, atol=2e-6)
    assert s["length"] == 7 and all(k.shape == (2, 4, 7, 6) for k, v in s["kv"])
