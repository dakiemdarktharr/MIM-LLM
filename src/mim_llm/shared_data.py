"""Same-split general format warm-up; no benchmark state labels or fitting."""

from __future__ import annotations

import re
from pathlib import Path

from .q3a.io import (
    read_json,
    read_rows,
    sha256,
    signature,
    source_sha256,
    write_json,
    write_rows,
)


def validate_source_groups(rows):
    groups = {}
    for row in rows:
        group = row.get("origin_source_id", row["source_id"])
        if group in groups and groups[group] != row["split"]:
            raise ValueError("An original source crosses warm-up splits")
        groups[group] = row["split"]


def prepare_format_warmup(original, output):
    original = Path(original)
    metadata = read_json(str(original) + ".manifest.json")
    if sha256(original) != metadata["sha256"]:
        raise ValueError("Original corpus checksum changed")
    rows = read_rows(original)
    validate_source_groups(rows)
    out = []
    seen = {signature(r["text"]) for r in rows}
    counts = {s: 0 for s in ("train", "validation", "test")}
    formats = dict.fromkeys(counts, 0)
    for r in rows:
        base = {**r, "origin_source_id": r["source_id"], "variant": "original"}
        out.append(base)
        seen.add(signature(r["text"]))
        counts[r["split"]] += 1
        text = r["text"].strip()
        if "..." in text or re.search(r"\b(?:Mr|Mrs|Dr)\.", text):
            continue
        parts = re.findall(r"[^.!?]+[.!?]", text)
        if len(parts) < 3 or any(len(x.split()) < 3 for x in parts[:3]):
            continue
        response = " ".join(x.strip() for x in parts[:3])
        if len(response.encode()) > 600 or '"' in response:
            continue
        example = "Write a short story in three sentences.\nContinuation:\n" + response
        if signature(example) in seen:
            continue
        seen.add(signature(example))
        out.append(
            {
                **r,
                "source_id": r["source_id"] + "-format3",
                "origin_source_id": r["source_id"],
                "text": example,
                "variant": "general_three_sentence_format",
            }
        )
        counts[r["split"]] += 1
        formats[r["split"]] += 1
    validate_source_groups(out)
    write_rows(output, out)
    manifest = {
        "dataset": metadata["dataset"]
        + " + mechanically derived general format examples",
        "revision": metadata["revision"],
        "license": metadata["license"],
        "source": metadata["source"],
        "counts": counts,
        "format_rows": formats,
        "underlying_source_counts": metadata["counts"],
        "original_corpus": original.as_posix(),
        "original_corpus_sha256": sha256(original),
        "original_manifest_signature": signature(metadata),
        "sha256": sha256(output),
        "transformation_code_sha256": source_sha256(__file__),
        "benchmark_state_labels_added": False,
        "tokenizer_fitted": False,
        "model_training_performed": False,
    }
    write_json(str(output) + ".manifest.json", manifest)
    return manifest


def general_rows(warmup):
    m = read_json(str(warmup) + ".manifest.json")
    if not m.get("original_corpus"):
        return read_rows(warmup)
    original = Path(m["original_corpus"])
    if (
        sha256(original) != m["original_corpus_sha256"]
        or signature(read_json(str(original) + ".manifest.json"))
        != m["original_manifest_signature"]
    ):
        raise ValueError("Original held-out general-text corpus changed")
    return read_rows(original)
