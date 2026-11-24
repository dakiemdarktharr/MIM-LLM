"""Story-level splits and shifted next-byte language-model batches."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import Dataset

from .tokenizer import Tokenizer


def stable_split(source_id: str) -> str:
    """Split by source story, keeping counterfactual variants together."""
    bucket = (
        int.from_bytes(hashlib.sha256(source_id.encode()).digest()[:4], "big") % 100
    )
    return "train" if bucket < 80 else "validation" if bucket < 90 else "test"


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row.get("text"), str) or not row["text"]:
                raise ValueError(f"{path}:{line_number}: nonempty text required")
            if not isinstance(row.get("source_id"), str) or not row["source_id"]:
                raise ValueError(f"{path}:{line_number}: source_id required")
            split = row.get("split", stable_split(row["source_id"]))
            if split not in {"train", "validation", "test"}:
                raise ValueError(f"{path}:{line_number}: invalid split")
            row["split"] = split
            rows.append(row)
    return rows


def assert_disjoint_sources(rows: list[dict[str, Any]]) -> None:
    by_source: dict[str, str] = {}
    by_text: dict[str, str] = {}
    for row in rows:
        source, split = row["source_id"], row["split"]
        if source in by_source and by_source[source] != split:
            raise ValueError(f"Source {source} occurs in multiple splits")
        by_source[source] = split
        digest = hashlib.sha256(row["text"].encode("utf-8")).hexdigest()
        if digest in by_text and by_text[digest] != split:
            raise ValueError("Identical story text occurs in multiple splits")
        by_text[digest] = split


class StoryDataset(Dataset):
    def __init__(
        self, rows: list[dict[str, Any]], tokenizer: Tokenizer, split: str, context: int
    ) -> None:
        if context < 2:
            raise ValueError("context must be at least 2")
        assert_disjoint_sources(rows)
        self.samples: list[tuple[list[int], list[int] | None, str]] = []
        for row in rows:
            if row["split"] != split:
                continue
            encoded = tokenizer.encode(row["text"], bos=True, eos=True)
            labels = row.get("state_labels")
            if labels is not None:
                if row.get("state_label_granularity") == "utf8_byte":
                    labels = tokenizer.align_byte_labels(row["text"], labels)
                elif row.get("state_label_granularity") not in (None, "token"):
                    raise ValueError("Unknown state_label_granularity")
                if len(labels) != len(encoded):
                    raise ValueError(
                        f"state_labels must align with encoded tokens for {row['source_id']}"
                    )
            # Each contiguous window predicts its following token. The first
            # token of a new window is context only, so target bytes are unique.
            for start in range(0, len(encoded) - 1, context):
                chunk = encoded[start : start + context + 1]
                if len(chunk) > 1:
                    state_chunk = (
                        labels[start : start + len(chunk) - 1]
                        if labels is not None
                        else None
                    )
                    self.samples.append((chunk, state_chunk, row["source_id"]))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[list[int], list[int] | None, str]:
        return self.samples[index]


def collate(samples: list[tuple[list[int], list[int] | None, str]]) -> dict[str, Any]:
    if not samples:
        raise ValueError("Empty batch")
    length = max(len(chunk) - 1 for chunk, _, _ in samples)
    batch = len(samples)
    inputs = torch.full((batch, length), 0, dtype=torch.long)
    targets = torch.full((batch, length), -100, dtype=torch.long)
    mask = torch.zeros((batch, length), dtype=torch.bool)
    states = torch.full((batch, length), -100, dtype=torch.long)
    for i, (chunk, state_labels, _) in enumerate(samples):
        valid = len(chunk) - 1
        inputs[i, :valid] = torch.tensor(chunk[:-1])
        targets[i, :valid] = torch.tensor(chunk[1:])
        mask[i, :valid] = True
        if state_labels is not None:
            states[i, :valid] = torch.tensor(state_labels)
    return {
        "input_ids": inputs,
        "targets": targets,
        "attention_mask": mask,
        "state_labels": states,
        "source_ids": [item[2] for item in samples],
    }
