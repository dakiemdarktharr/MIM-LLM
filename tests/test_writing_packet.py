"""Synthetic serialization fixtures, never real model/human evidence."""

import csv

import pytest

from mim_llm.q3a.io import (
    read_json,
    read_rows,
    sha256,
    signature,
    write_json,
    write_rows,
)
from mim_llm.q3a_subword.writing_packet import make_packet


def fixture_panel(tmp_path, *, corrupt=False):
    directory = tmp_path / "synthetic-unit-panel"
    directory.mkdir()
    prompts = [
        {
            "condition": "conditional",
            "source_id": f"fixture-{i}",
            "prompt": f"Synthetic prefix {i}.\n",
        }
        for i in range(16)
    ]
    prompts.append(
        {"condition": "unconditional", "source_id": None, "prompt": "Write a story.\n"}
    )
    manifest = {
        "plan_id": "synthetic-fixture",
        "prompts": prompts,
        "expected_samples": 34,
    }
    manifest["review_id"] = signature(manifest)
    manifest_path = tmp_path / "manifest.json"
    write_json(manifest_path, manifest)
    parents = {
        "foundation-mingru-s0": "fixture-hash-a",
        "foundation-transformer-s0": "fixture-hash-b",
    }
    rows = [
        {
            **p,
            "run_id": run,
            "plan_id": manifest["plan_id"],
            "review_id": manifest["review_id"],
            "checkpoint_sha256": digest,
            "continuation": "" if i == 0 else f"Synthetic output {i}.",
            "human_label": None,
            "primary_evaluation": False,
        }
        for run, digest in parents.items()
        for i, p in enumerate(prompts)
    ]
    if corrupt:
        rows[0]["prompt"] = "Undeclared replacement prompt"
    write_rows(directory / "samples.jsonl", rows)
    write_json(
        directory / "started.json",
        {
            "manifest_sha256": sha256(manifest_path),
            "review_id": manifest["review_id"],
            "plan_id": manifest["plan_id"],
            "checkpoint_sha256": parents,
        },
    )
    write_json(
        directory / "completed.json",
        {
            "complete": True,
            "samples": 34,
            "review_id": manifest["review_id"],
            "samples_sha256": sha256(directory / "samples.jsonl"),
        },
    )
    return directory, manifest_path


def test_writing_packet_hides_run_ids_and_prefills_no_labels(tmp_path):
    directory, manifest = fixture_panel(tmp_path)
    output = tmp_path / "packet"
    result = make_packet(directory, manifest, output)
    packet = read_rows(output / "packet.jsonl")
    key = read_rows(output / "PRIVATE-key.jsonl")
    assert len(packet) == len(key) == result["items"] == 34
    assert all(set(r) == {"item_id", "prompt", "continuation"} for r in packet)
    assert sum(r["continuation"] == "" for r in packet) == 2
    assert result["real_labels_collected"] == 0
    assert result["independent_reader_validation"] is False
    assert read_json(output / "receipt.json")["writing_gate_passed"] is None
    with (output / "reader-author.csv").open(newline="", encoding="utf-8") as f:
        labels = list(csv.DictReader(f))
    assert all(
        r["item_id"] and all(not v for k, v in r.items() if k != "item_id")
        for r in labels
    )
    with pytest.raises(FileExistsError):
        make_packet(directory, manifest, output)


def test_valid_hashes_do_not_allow_replaced_review_prompt(tmp_path):
    directory, manifest = fixture_panel(tmp_path, corrupt=True)
    with pytest.raises(ValueError, match="provenance"):
        make_packet(directory, manifest, tmp_path / "packet")
    assert not (tmp_path / "packet").exists()


def test_incomplete_review_cannot_be_presented_as_human_packet(tmp_path):
    directory, manifest = fixture_panel(tmp_path)
    receipt = read_json(directory / "completed.json")
    receipt["complete"] = False
    write_json(directory / "completed.json", receipt, replace=True)
    with pytest.raises(ValueError, match="complete"):
        make_packet(directory, manifest, tmp_path / "packet")
