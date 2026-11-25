"""General format preparation is a deterministic data transform, not training."""

import pytest

from mim_llm.q3a.io import read_rows, sha256, write_json, write_rows
from mim_llm.shared_data import (
    general_rows,
    prepare_format_warmup,
    validate_source_groups,
)


def test_general_format_examples_keep_original_splits_and_ppl_corpus(tmp_path):
    original = tmp_path / "original.jsonl"
    rows = [
        {
            "source_id": "unit-" + s,
            "split": s,
            "text": name + " saw a flower. It grew in a garden. The day was warm.",
        }
        for s, name in [("train", "Lan"), ("validation", "Mai"), ("test", "Huy")]
    ]
    write_rows(original, rows)
    write_json(
        str(original) + ".manifest.json",
        {
            "dataset": "UNIT",
            "revision": "unit",
            "license": "UNIT-ONLY",
            "source": "UNIT",
            "counts": dict.fromkeys(("train", "validation", "test"), 1),
            "sha256": sha256(original),
        },
    )
    output = tmp_path / "mix.jsonl"
    m = prepare_format_warmup(original, output)
    mixed = read_rows(output)
    assert len(mixed) == 6 and all(n == 1 for n in m["format_rows"].values())
    assert (
        m["model_training_performed"] is False
        and m["benchmark_state_labels_added"] is False
    )
    for row in mixed:
        assert (
            next(r["split"] for r in rows if r["source_id"] == row["origin_source_id"])
            == row["split"]
        )
    assert general_rows(output) == rows
    with pytest.raises(FileExistsError):
        prepare_format_warmup(original, output)


def test_original_source_cannot_cross_format_splits():
    with pytest.raises(ValueError):
        validate_source_groups(
            [
                {"source_id": "a", "origin_source_id": "root", "split": "train"},
                {"source_id": "a-format", "origin_source_id": "root", "split": "test"},
            ]
        )
