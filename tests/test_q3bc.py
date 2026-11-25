"""Synthetic contract fixtures only; no production training/human annotations."""

import copy
import importlib

import pytest
import torch

from mim_llm.models import ModelConfig, build_model
from mim_llm.q3a.io import read_rows, sha256, signature, write_json, write_rows
from mim_llm.q3bc.bank import constrained_history, history_surprisal, seal
from mim_llm.q3bc.data import (
    b_probe,
    b_source,
    c_source,
    history_options,
    parse_controlled_history,
    prepare,
    verify,
)
from mim_llm.q3bc.objectives import examples_for, loss_batch
from mim_llm.q3bc.runner import execute
from mim_llm.training_gate import TrainingNotAuthorized


@pytest.mark.parametrize("index", range(16))
def test_b_exact_delay_labels_and_no_answer_leak(index):
    row = b_source(f"unit-{index}", "train", 2026, index)
    lo = b_probe(row, "B1", index)
    hi = b_probe(row, "B2", index)
    now = b_probe(row, "B0", index)
    assert lo["token_delay"] == hi["token_delay"] == 256 and now["token_delay"] == 0
    assert lo["semantic_writes"] == 0 and hi["semantic_writes"] == 6
    assert lo["reference"] == hi["reference"] == now["reference"]
    assert "Question:" not in row["event_text"] and "Answer:" not in row["event_text"]
    assert all(e["object"] != row["subject"] for e in row["events"])
    assert row["prompt"].startswith(
        row["event_text"][: row["windows"]["high"]["probe_end"]]
    )
    assert (
        row["continuation_cut"] - row["windows"]["high"]["evidence_end"] == row["lag"]
    )


@pytest.mark.parametrize("study", ["b", "c"])
def test_bc_integrity_and_disjoint_sources(study, tmp_path):
    d = tmp_path / study
    manifest = prepare(study, d, train_sources=8, validation_sources=3, test_sources=3)
    assert verify(d) == manifest
    texts = [
        r.get("event_text", r["prompt"])
        for s in ("train", "validation", "test")
        for r in read_rows(d / (s + ".jsonl"))
    ]
    assert len(texts) == len(set(texts))
    with pytest.raises(FileExistsError):
        prepare(study, d)
    with (d / "test.jsonl").open("a") as f:
        f.write("\n")
    with pytest.raises(ValueError):
        verify(d)


@pytest.mark.parametrize("kind", ["mingru", "transformer"])
@pytest.mark.parametrize("arm", ["B0", "B1", "B2", "B3"])
def test_b_gradients_and_token_cap_without_updates(kind, arm):
    model = build_model(ModelConfig(kind=kind, width=8, layers=2, context=2048))
    before = {k: p.detach().clone() for k, p in model.named_parameters()}
    p = {"study": "b", "config": {"context": 2048, "answer_loss_weight": 0.25}}
    items = [{"row": b_source("unit", "train", 8, 1), "source_id": "unit", "index": 1}]
    loss, n, counts = loss_batch(model, items, p, {"arm": arm}, remaining=25)
    assert n == 25 and counts["answer_targets"] == 6 and counts["event_targets"] == 19
    loss.backward()
    assert torch.isfinite(loss)
    assert all(torch.equal(v, before[k]) for k, v in model.named_parameters())
    assert all(
        x.grad is not None and torch.isfinite(x.grad).all() for x in model.parameters()
    )


def test_b_future_stream_edits_do_not_change_probe_input():
    row = b_source("unit", "train", 8, 0)
    probe = b_probe(row, "B1", 0)
    other = copy.deepcopy(row)
    end = row["windows"]["low"]["probe_end"]
    other["event_text"] = row["event_text"][:end] + "Different future."
    assert b_probe(other, "B1", 0)["prompt"] == probe["prompt"]


def test_b_immediate_probe_counterbalances_absolute_window_position():
    positions = []
    for i in range(4):
        row = b_source(f"unit-{i}", "train", 8, i)
        p = b_probe(row, "B0", i)
        first = min(w["evidence_end"] for w in row["windows"].values())
        positions.append(p["prefix_bytes"] == first)
    assert positions.count(True) == positions.count(False) == 2


@pytest.mark.parametrize("kind", ["mingru", "transformer"])
def test_c_constrained_autoregression_is_inference_only(kind):
    row = c_source("unit", "train", 8, 1)
    model = build_model(ModelConfig(kind=kind, width=8, layers=2, context=2048)).eval()
    before = {k: p.detach().clone() for k, p in model.named_parameters()}
    h = constrained_history(model, row, seed=23)
    assert h["text"] in {x["text"] for x in history_options(row)}
    assert parse_controlled_history(row, h["text"])["place"] == h["place"]
    assert history_surprisal(model, row, h) >= 0
    assert all(torch.equal(p, before[k]) for k, p in model.named_parameters())
    assert parse_controlled_history(row, "not " + h["text"]) is None


def test_c_teacher_fixture_cannot_become_self_training_data(tmp_path):
    d = tmp_path / "c"
    prepare("c", d, train_sources=2, validation_sources=1, test_sources=1)
    p = {"study": "c", "data_dir": str(d), "sealed_bank": None}
    with pytest.raises(ValueError, match="Genuine"):
        examples_for(p, {"id": "C2-mingru-s0"})
    assert all(
        x["contract_fixture"] for x in examples_for(p, {}, contract_fixture=True)
    )


def test_bc_training_gate_runs_before_io(tmp_path):
    for run in ("B1-mingru-s0", "C2-mingru-s0"):
        with pytest.raises(TrainingNotAuthorized):
            execute("missing", run, tmp_path / "out", seconds_limit=1)
    assert not list(tmp_path.iterdir())


def test_c_matching_and_actual_event_suffixes_with_fictional_fixtures(
    tmp_path, monkeypatch
):
    # These manually constructed grammar records exist only in a unit-test temp directory.
    from mim_llm.tokenizer import ByteTokenizer

    d = tmp_path / "data"
    dm = prepare("c", d, train_sources=4, validation_sources=1, test_sources=1)
    rows = read_rows(d / "train.jsonl")
    raw = tmp_path / "raw"
    raw.mkdir()
    hashes = {}
    digests = {}
    for kind in ("mingru", "transformer"):
        for seed in (0, 1, 2):
            digest = f"UNIT-{kind}-{seed}"
            digests[f"{kind}/s{seed}"] = digest
            hist = []
            for row in rows:
                h = next(
                    h
                    for h in history_options(row)
                    if h["place"] == "drawer" and h["style"] == seed
                )
                hist.append(
                    {
                        "source_id": row["source_id"],
                        **h,
                        "token_ids": ByteTokenizer().encode(h["text"]),
                        "checkpoint_sha256": digest,
                        "prompt_sha256": signature(row["prompt"]),
                        "seed": seed,
                        "kind": kind,
                    }
                )
            path = raw / f"{kind}-s{seed}.jsonl"
            write_rows(path, hist)
            hashes[path.name] = sha256(path)
    manifest = {
        "shared_plan_id": "UNIT",
        "dataset_id": dm["dataset_id"],
        "sha256": hashes,
        "checkpoint_sha256": digests,
    }
    manifest["bank_id"] = signature(manifest)
    write_json(raw / "manifest.json", manifest)
    module = importlib.import_module("mim_llm.q3bc.bank")
    monkeypatch.setattr(
        module,
        "load_initialization_plan",
        lambda p: {
            "plan_id": "UNIT",
            "config": {"backbones": ["mingru", "transformer"], "seeds": [0, 1, 2]},
        },
    )
    monkeypatch.setattr(
        module,
        "load_initialization",
        lambda p, r, k, s, d: (None, digests[f"{k}/s{s}"]),
    )
    monkeypatch.setattr(module, "history_surprisal", lambda *a, **k: 1.0)
    out = tmp_path / "sealed"
    result = seal("unit", d, "unit", raw, out, minimum_sources=2)
    assert result["ready"] and len(result["sha256"]) == 24
    a = read_rows(out / "C1-mingru-s0.jsonl")
    b = read_rows(out / "C2-mingru-s0.jsonl")
    assert all(
        x["reference"] == y["reference"] and x["place"] == y["place"] == "drawer"
        for x, y in zip(a, b)
    )
