"""One bounded Q3-A language-initialization repair; preserve old source splits.

This is data preparation, with no model updates, tokenizer fitting or test
evaluation. Derived rows inherit their complete original story's split.
"""

from __future__ import annotations

import hashlib
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
from .shared_data import validate_source_groups


def text_digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def expand_preserving_splits(original, output, *, train_stories, stream=None):
    """Retain every old row and exclude all old held-out texts from additions."""
    original, output = Path(original), Path(output)
    metadata = read_json(str(original) + ".manifest.json")
    if output.exists() or Path(str(output) + ".manifest.json").exists():
        raise FileExistsError(output)
    if sha256(original) != metadata["sha256"]:
        raise ValueError("Changed original corpus")
    rows = read_rows(original)
    validate_source_groups(rows)
    if len({r["source_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate original source IDs")
    seen = {text_digest(r["text"]) for r in rows}
    if len(seen) != len(rows):
        raise ValueError("Duplicate original texts")
    counts = {
        s: sum(r["split"] == s for r in rows) for s in ("train", "validation", "test")
    }
    if train_stories <= counts["train"]:
        raise ValueError("This amendment must expand the training corpus")
    if stream is None:
        from datasets import load_dataset

        stream = load_dataset(
            metadata["dataset"],
            split="train",
            streaming=True,
            revision=metadata["revision"],
        ).shuffle(seed=metadata["stream_shuffle_seed"], buffer_size=10_000)
    duplicates = 0
    for item in stream:
        text = item.get("text")
        if not isinstance(text, str) or not text.strip():
            continue
        digest = text_digest(text)
        if digest in seen:
            duplicates += 1
            continue
        seen.add(digest)
        rows.append(
            {
                "source_id": "tinystories-" + digest[:24],
                "split": "train",
                "text": text,
                "origin": metadata["dataset"],
                "revision": metadata["revision"],
                "license": metadata["license"],
            }
        )
        counts["train"] += 1
        if counts["train"] == train_stories:
            break
    else:
        raise ValueError("Insufficient distinct train stories; no output written")
    if len({r["source_id"] for r in rows}) != len(rows):
        raise ValueError("Source ID collision")
    # Prefix equality proves that the old rows, not just their counts, survived.
    old = read_rows(original)
    if rows[: len(old)] != old:
        raise ValueError("An existing source was changed")
    write_rows(output, rows)
    manifest = {
        **metadata,
        "counts": counts,
        "sha256": sha256(output),
        "expansion": {
            "previous_corpus": original.as_posix(),
            "previous_corpus_sha256": sha256(original),
            "previous_manifest_signature": signature(metadata),
            "all_previous_rows_retained_verbatim": True,
            "all_previous_heldout_text_hashes_excluded_from_new_train": True,
            "new_sources_only_from_upstream_train": True,
            "duplicate_texts_skipped": duplicates,
            "near_duplicate_exclusion_claimed": False,
            "transformation_source_sha256": source_sha256(__file__),
        },
    }
    write_json(str(output) + ".manifest.json", manifest)
    return manifest


def prepare_continuation_warmup(original, output, *, context=2048):
    """Original text + unconditioned format + prefix-conditioned next 3 sentences.

    Sentence selection is conservative and mechanical, not human annotation.
    The normal causal LM objective predicts the entire row; no state supervision
    or response-only objective is introduced by this calibration amendment.
    """
    original, output = Path(original), Path(output)
    metadata = read_json(str(original) + ".manifest.json")
    if output.exists() or Path(str(output) + ".manifest.json").exists():
        raise FileExistsError(output)
    if sha256(original) != metadata["sha256"]:
        raise ValueError("Changed expanded corpus")
    rows = read_rows(original)
    validate_source_groups(rows)
    seen = {signature(r["text"]) for r in rows}
    out = []
    counts = dict.fromkeys(("train", "validation", "test"), 0)
    variants = {s: {"unconditional": 0, "conditional": 0} for s in counts}
    for r in rows:
        out.append({**r, "origin_source_id": r["source_id"], "variant": "original"})
        counts[r["split"]] += 1
        text = r["text"].strip()
        if '"' in text or "..." in text or re.search(r"\b(?:Mr|Mrs|Dr)\.", text):
            continue
        parts = [p.strip() for p in re.findall(r"[^.!?]+[.!?]", text)]
        if len(parts) < 3 or any(len(p.split()) < 3 for p in parts[:3]):
            continue
        candidates = [
            (
                "unconditional",
                "Write a short story in three sentences.\nContinuation:\n",
                " ".join(parts[:3]),
            )
        ]
        if len(parts) >= 5 and all(len(p.split()) >= 3 for p in parts[3:5]):
            candidates.append(
                (
                    "conditional",
                    " ".join(parts[:2])
                    + "\nContinue this story in three to five sentences.\nContinuation:\n",
                    " ".join(parts[2:5]),
                )
            )
        for kind, prompt, response in candidates:
            example = prompt + response
            # Byte tokenizer: BOS+text+EOS -> one fewer next-token targets.
            if (
                len(response.encode("utf-8")) > 600
                or len(example.encode("utf-8")) + 1 > context
            ):
                continue
            digest = signature(example)
            if digest in seen:
                continue
            seen.add(digest)
            out.append(
                {
                    **r,
                    "source_id": r["source_id"] + "-calibration-" + kind,
                    "origin_source_id": r["source_id"],
                    "text": example,
                    "variant": "general_three_sentence_" + kind,
                    "prompt": prompt,
                    "response": response,
                }
            )
            counts[r["split"]] += 1
            variants[r["split"]][kind] += 1
    validate_source_groups(out)
    write_rows(output, out)
    manifest = {
        "dataset": metadata["dataset"] + " + bounded continuation calibration examples",
        "revision": metadata["revision"],
        "license": metadata["license"],
        "source": metadata["source"],
        "counts": counts,
        "format_rows": variants,
        "underlying_source_counts": metadata["counts"],
        "original_corpus": original.as_posix(),
        "original_corpus_sha256": sha256(original),
        "original_manifest_signature": signature(metadata),
        "sha256": sha256(output),
        "transformation_code_sha256": source_sha256(__file__),
        "all_previous_heldouts_preserved": True,
        "benchmark_state_labels_added": False,
        "tokenizer_fitted": False,
        "model_training_performed": False,
        "human_sentence_labels": False,
        "objective": "causal next-token CE over entire rows, including instruction prefixes",
    }
    write_json(str(output) + ".manifest.json", manifest)
    return manifest
