"""Invented temporary fixtures only: no research outputs or human ratings."""

import csv
from pathlib import Path

import pytest
from test_writing_packet import fixture_panel

from mim_llm.q3a.io import read_json, read_rows, sha256, write_json, write_rows
from mim_llm.q3a_subword import writing_decision as decision
from mim_llm.q3a_subword.writing_packet import FIELDS, make_packet


def setup_screen(tmp_path, monkeypatch):
    directory, manifest = fixture_panel(tmp_path)
    packet = tmp_path / "packet"
    make_packet(directory, manifest, packet)
    original = (
        Path(__file__).resolve().parents[1] / "configs/q3a/foundation_writing_rule.json"
    )
    rule = read_json(original)
    review = read_json(manifest)
    rule.update(review_id=review["review_id"], foundation_plan_id=review["plan_id"])
    rule_path = tmp_path / "synthetic-rule.json"
    write_json(rule_path, rule)
    monkeypatch.setattr(decision, "RULE_SHA256", sha256(rule_path))
    labels = packet / "reader-author.csv"
    return directory, manifest, packet, labels, rule_path


def save_labels(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def invented_ratings(packet):
    return [
        {
            "item_id": r["item_id"],
            "rater_id": "SYNTHETIC_UNIT_FIXTURE_NOT_A_HUMAN",
            "format_3_to_5": "1",
            "fluency_1_to_5": "3",
            "follows_prefix": "1",
            "new_event": "1",
            "self_consistent": "1",
            "unclear": "0",
            "evidence": "Invented temporary fixture, not a real judgment.",
            "elapsed_seconds": "1",
        }
        for r in read_rows(packet / "packet.jsonl")
    ]


def test_real_prospective_rule_bytes_are_pinned():
    root = Path(__file__).resolve().parents[1]
    assert (
        sha256(root / "configs/q3a/foundation_writing_rule.json")
        == decision.RULE_SHA256
    )


def test_blank_and_partial_ratings_remain_pending(tmp_path, monkeypatch):
    args = setup_screen(tmp_path, monkeypatch)
    result = decision.decide(*args)
    assert result["decision"] == "pending" and result["complete_rating_records"] == 0
    rows = invented_ratings(args[2])[:33]
    save_labels(args[3], rows)
    result = decision.decide(*args)
    assert result["complete_rating_records"] == 33
    assert result["writing_screen_passed"] is None
    assert all(r["screen_passed"] is None for r in result["by_run"].values())


@pytest.mark.parametrize("replace_receipt_hash", [False, True])
def test_replaced_display_text_rejected_even_when_hash_is_updated(
    tmp_path, monkeypatch, replace_receipt_hash
):
    args = setup_screen(tmp_path, monkeypatch)
    readable = args[2] / "reader-packet.md"
    readable.write_text("Replaced text is not a real generation.", encoding="utf-8")
    if replace_receipt_hash:
        receipt = read_json(args[2] / "receipt.json")
        receipt["reader_markdown_sha256"] = sha256(readable)
        write_json(args[2] / "receipt.json", receipt, replace=True)
    with pytest.raises(ValueError, match="Displayed Markdown"):
        decision.decide(*args)


def test_unconditional_failure_is_not_rescued_by_conditional_ratings(
    tmp_path, monkeypatch
):
    args = setup_screen(tmp_path, monkeypatch)
    rows = invented_ratings(args[2])
    save_labels(args[3], rows)
    result = decision.decide(*args)
    assert result["decision"] == "pass"
    key = read_rows(args[2] / "PRIVATE-key.jsonl")
    unconditional = next(k["item_id"] for k in key if k["condition"] == "unconditional")
    next(r for r in rows if r["item_id"] == unconditional)["follows_prefix"] = "0"
    save_labels(args[3], rows)
    result = decision.decide(*args)
    assert result["decision"] == "fail"
    assert result["post_training_authorized"] is False
    assert result["independent_reader_validation"] is False


@pytest.mark.parametrize(
    "field,value", [("elapsed_seconds", "nan"), ("unclear", "yes")]
)
def test_invalid_ratings_are_not_dropped(tmp_path, monkeypatch, field, value):
    args = setup_screen(tmp_path, monkeypatch)
    rows = invented_ratings(args[2])
    rows[0][field] = value
    save_labels(args[3], rows)
    with pytest.raises(ValueError):
        decision.decide(*args)


def test_swapped_hidden_mapping_rejected_even_with_valid_public_hash(
    tmp_path, monkeypatch
):
    args = setup_screen(tmp_path, monkeypatch)
    path = args[2] / "PRIVATE-key.jsonl"
    rows = read_rows(path)
    rows[0]["item_id"], rows[1]["item_id"] = rows[1]["item_id"], rows[0]["item_id"]
    path.unlink()
    write_rows(path, rows)
    with pytest.raises(ValueError, match="replaced"):
        decision.decide(*args)


def test_duplicate_normalization_counts_surface_only_variation():
    assert decision.normalized("Ａ Story\n HERE") == decision.normalized(
        "a  story here"
    )


def test_repetitive_outputs_cannot_pass_on_positive_ratings_alone(
    tmp_path, monkeypatch
):
    args = list(setup_screen(tmp_path, monkeypatch))
    samples = read_rows(args[0] / "samples.jsonl")
    for row in samples[:5]:
        row["continuation"] = (
            "Ａ Story\n HERE" if row["source_id"] == "fixture-0" else "a story here"
        )
    (args[0] / "samples.jsonl").unlink()
    write_rows(args[0] / "samples.jsonl", samples)
    completion = read_json(args[0] / "completed.json")
    completion["samples_sha256"] = sha256(args[0] / "samples.jsonl")
    write_json(args[0] / "completed.json", completion, replace=True)
    args[2] = tmp_path / "packet-repetitive-fixture"
    make_packet(args[0], args[1], args[2])
    args[3] = args[2] / "reader-author.csv"
    save_labels(args[3], invented_ratings(args[2]))
    result = decision.decide(*args)
    assert result["decision"] == "fail"
    assert (
        max(
            r["largest_normalized_identical_conditional_group"]
            for r in result["by_run"].values()
        )
        == 5
    )


def test_each_backbone_must_reach_twelve_conditional_joint_passes(
    tmp_path, monkeypatch
):
    args = setup_screen(tmp_path, monkeypatch)
    rows = invented_ratings(args[2])
    key = read_rows(args[2] / "PRIVATE-key.jsonl")
    failed = {
        k["item_id"]
        for k in key
        if k["run_id"] == "foundation-mingru-s0" and k["condition"] == "conditional"
    }
    for row in [r for r in rows if r["item_id"] in failed][:5]:
        row["new_event"] = "0"
    save_labels(args[3], rows)
    result = decision.decide(*args)
    assert result["decision"] == "fail"
    assert result["by_run"]["foundation-mingru-s0"]["conditional_joint_passes"] == 11
    assert (
        result["by_run"]["foundation-transformer-s0"]["conditional_joint_passes"] == 16
    )


def test_changed_rule_cannot_retroactively_pass(tmp_path, monkeypatch):
    args = setup_screen(tmp_path, monkeypatch)
    rule = read_json(args[-1])
    rule["per_backbone_minimum_joint_passes"] = 0
    write_json(args[-1], rule, replace=True)
    with pytest.raises(ValueError, match="thresholds"):
        decision.decide(*args)
