"""Optional, pinned streaming import of a bounded TinyStories subset."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def fetch_tinystories(
    output: str,
    *,
    train_stories: int,
    validation_stories: int,
    test_stories: int,
    seed: int = 2026,
    revision: str | None = None,
) -> dict[str, Any]:
    if min(train_stories, validation_stories, test_stories) < 1:
        raise ValueError("Each subset count must be positive")
    try:
        from datasets import load_dataset
        from huggingface_hub import HfApi
    except ImportError as exc:
        raise RuntimeError(
            "Install the optional data extra: pip install -e .[data]"
        ) from exc
    destination = Path(output)
    if destination.exists():
        raise FileExistsError(destination)
    dataset_id = "roneneldan/TinyStories"
    pinned_revision = revision or HfApi().dataset_info(dataset_id).sha
    seen: set[str] = set()
    counts = {"train": 0, "validation": 0, "test": 0}
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        for source_split, assignments in (
            ("train", (("train", train_stories),)),
            (
                "validation",
                (("validation", validation_stories), ("test", test_stories)),
            ),
        ):
            stream = load_dataset(
                dataset_id, split=source_split, streaming=True, revision=pinned_revision
            )
            stream = stream.shuffle(seed=seed, buffer_size=10_000)
            assignment = iter(assignments)
            target_split, wanted = next(assignment)
            for item in stream:
                text = item.get("text")
                if not isinstance(text, str) or not text.strip():
                    continue
                digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
                if digest in seen:
                    continue
                seen.add(digest)
                handle.write(
                    json.dumps(
                        {
                            "source_id": f"tinystories-{digest[:24]}",
                            "split": target_split,
                            "text": text,
                            "origin": dataset_id,
                            "revision": pinned_revision,
                            "license": "cdla-sharing-1.0",
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                counts[target_split] += 1
                if counts[target_split] == wanted:
                    try:
                        target_split, wanted = next(assignment)
                    except StopIteration:
                        break
            else:
                raise RuntimeError(
                    f"Could not collect requested {source_split} stories"
                )
    manifest = {
        "dataset": dataset_id,
        "revision": pinned_revision,
        "license": "cdla-sharing-1.0",
        "stream_shuffle_seed": seed,
        "counts": counts,
        "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "source": "https://huggingface.co/datasets/roneneldan/TinyStories",
    }
    destination.with_suffix(destination.suffix + ".manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest
