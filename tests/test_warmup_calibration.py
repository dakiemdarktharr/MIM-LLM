"""Nontraining checks for hold-out protection and actual continuation targets."""

import pytest

from mim_llm.q3a.io import read_rows, sha256, write_json, write_rows
from mim_llm.shared_data import general_rows
from mim_llm.warmup_calibration import (
    expand_preserving_splits,
    prepare_continuation_warmup,
    text_digest,
)


def corpus(tmp_path):
    path = tmp_path / "old.jsonl"
    rows = [
        {
            "source_id": "tinystories-" + text_digest(text)[:24],
            "text": text,
            "split": split,
            "origin": "fixture",
            "revision": "fixture-revision",
            "license": "fixture-only",
        }
        for split, text in (
            (
                "train",
                "Amy found a ball. She took it home. It was very red. Amy saw her friend. They played all day.",
            ),
            (
                "validation",
                "Ben found a ball. He took it home. It was very blue. Ben saw his friend. They played all day.",
            ),
            (
                "test",
                "Cara found a ball. She took it home. It was very green. Cara saw her friend. They played all day.",
            ),
        )
    ]
    write_rows(path, rows)
    write_json(
        str(path) + ".manifest.json",
        {
            "dataset": "fixture",
            "revision": "fixture-revision",
            "license": "fixture-only",
            "source": "fixture",
            "stream_shuffle_seed": 2026,
            "counts": {"train": 1, "validation": 1, "test": 1},
            "sha256": sha256(path),
        },
    )
    return path, rows


def test_expansion_protects_all_old_sources(tmp_path):
    old, rows = corpus(tmp_path)
    destination = tmp_path / "expanded.jsonl"
    stream = [{"text": r["text"]} for r in reversed(rows)] + [
        {"text": "A new training story."}
    ]
    result = expand_preserving_splits(old, destination, train_stories=2, stream=stream)
    actual = read_rows(destination)
    assert actual[:3] == rows
    assert actual[-1]["split"] == "train"
    assert result["expansion"]["duplicate_texts_skipped"] == 3
    assert result["counts"] == {"train": 2, "validation": 1, "test": 1}
    with pytest.raises(FileExistsError):
        expand_preserving_splits(old, destination, train_stories=2, stream=[])


def test_insufficient_expansion_does_not_publish_partial_corpus(tmp_path):
    old, rows = corpus(tmp_path)
    destination = tmp_path / "expanded.jsonl"
    with pytest.raises(ValueError, match="Insufficient"):
        expand_preserving_splits(
            old, destination, train_stories=2, stream=[{"text": rows[2]["text"]}]
        )
    assert not destination.exists()


def test_conditional_rows_continue_prefix_not_restart_story(tmp_path):
    old, rows = corpus(tmp_path)
    destination = tmp_path / "warmup.jsonl"
    manifest = prepare_continuation_warmup(old, destination)
    actual = read_rows(destination)
    for r in actual:
        if r["variant"] == "general_three_sentence_conditional":
            original = next(x for x in rows if x["source_id"] == r["origin_source_id"])
            assert r["split"] == original["split"]
            assert "found a ball." in r["prompt"]
            assert "found a ball." not in r["response"]
            assert "took it home." in r["prompt"]
            assert "took it home." not in r["response"]
            assert r["response"].startswith("It was very")
            assert r["text"] == r["prompt"] + r["response"]
    assert manifest["format_rows"]["train"]["conditional"] == 1
    assert general_rows(destination) == rows
    assert manifest["benchmark_state_labels_added"] is False
