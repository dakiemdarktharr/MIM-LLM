"""Source-preserving corpus expansion and bounded-context uint16 token files."""

import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np

from ..q3a.io import read_json, read_rows, sha256, source_sha256, write_json
from ..warmup_calibration import expand_preserving_splits


def normalized_digest(text):
    text = " ".join(unicodedata.normalize("NFKC", text).casefold().split())
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def expand_normalized(original, output, *, train_stories, stream=None):
    old = read_rows(original)
    seen = {normalized_digest(r["text"]) for r in old}
    if len(seen) != len(old):
        raise ValueError("Original corpus already has normalized duplicates")
    metadata = read_json(str(original) + ".manifest.json")
    if stream is None:
        from datasets import load_dataset

        stream = load_dataset(
            metadata["dataset"],
            split="train",
            streaming=True,
            revision=metadata["revision"],
        ).shuffle(seed=metadata["stream_shuffle_seed"], buffer_size=10_000)
    skipped = [0]

    def distinct():
        for row in stream:
            text = row.get("text")
            if not isinstance(text, str) or not text.strip():
                continue
            digest = normalized_digest(text)
            if digest in seen:
                skipped[0] += 1
                continue
            seen.add(digest)
            yield row

    manifest = expand_preserving_splits(
        original, output, train_stories=train_stories, stream=distinct()
    )
    manifest["normalized_exclusion"] = {
        "rule": "NFKC/casefold/whitespace full-story digest; not semantic deduplication",
        "skipped_new_candidates": skipped[0],
        "all_old_rows_unchanged": True,
        "source_sha256": source_sha256(__file__),
    }
    write_json(str(output) + ".manifest.json", manifest, replace=True)
    return manifest


def language_windows(ids, context):
    """Reset each context window; cover every next-token label exactly once."""
    if context < 2 or len(ids) < 2:
        raise ValueError("Need nonempty shifted sequences and context>=2")
    for start in range(0, len(ids) - 1, context):
        yield start, min(context, len(ids) - 1 - start)


def instruction_candidates(text):
    if '"' in text or "..." in text or re.search(r"\b(?:Mr|Mrs|Dr)\.", text):
        return
    parts = [p.strip() for p in re.findall(r"[^.!?]+[.!?]", text.strip())]
    if len(parts) < 3 or any(len(p.split()) < 3 for p in parts[:3]):
        return
    yield (
        "unconditional",
        "Write a short story in three sentences.\nContinuation:\n",
        " ".join(parts[:3]),
    )
    if len(parts) >= 5 and all(len(p.split()) >= 3 for p in parts[3:5]):
        yield (
            "conditional",
            " ".join(parts[:2])
            + "\nContinue this story in three to five sentences.\nContinuation:\n",
            " ".join(parts[2:5]),
        )


def encode_corpus(corpus, destination, tokenizer, *, context=1024):
    """Encode train/validation only; retain long LM documents via reset windows.

    Each index row is [token_offset,input_length,first_supervised_position].
    Binary formats are explicitly little-endian uint16/int64. Test remains raw.
    """
    corpus, destination = Path(corpus), Path(destination)
    metadata = read_json(str(corpus) + ".manifest.json")
    if sha256(corpus) != metadata["sha256"]:
        raise ValueError("Corpus changed")
    if destination.exists():
        raise FileExistsError(destination)
    if tokenizer.vocab_size > 65536:
        raise ValueError("uint16 token storage cannot represent this vocabulary")
    destination.mkdir(parents=True)
    write_json(
        destination / "preparation-start.json",
        {
            "source_sha256": sha256(corpus),
            "optimizer_updates": 0,
            "test_performance_measured": False,
        },
    )
    indices = {
        (s, stage): [] for s in ("train", "validation") for stage in ("lm", "sft")
    }
    counters = {(s, stage): Counter() for s, stage in indices}
    handles = {}
    seen = set()
    try:
        for split, stage in indices:
            prefix = f"{split}-{stage}"
            handles[split, stage] = (
                (destination / (prefix + ".ids.u16")).open("xb"),
                (destination / (prefix + ".sources.jsonl")).open("x", encoding="utf-8"),
            )
        with corpus.open(encoding="utf-8") as raw:
            for line in raw:
                row = json.loads(line)
                source, split = row["source_id"], row["split"]
                if source in seen:
                    raise ValueError("Duplicate source ID")
                seen.add(source)
                if split == "test":
                    continue
                if split not in {"train", "validation"}:
                    raise ValueError("Unknown source split")
                ids = tokenizer.encode(row["text"], bos=True, eos=True)
                if tokenizer.eos_id in ids[1:-1]:
                    raise ValueError("Reserved token inside original story")
                binary, sources = handles[split, "lm"]
                offset = binary.tell() // 2
                binary.write(np.asarray(ids, dtype="<u2").tobytes())
                counters[split, "lm"]["sources"] += 1
                for start, length in language_windows(ids, context):
                    indices[split, "lm"].append((offset + start, length, 0))
                    counters[split, "lm"]["targets"] += length
                    sources.write(
                        json.dumps({"source_id": source, "window_start": start}) + "\n"
                    )
                for variant, prompt, response in instruction_candidates(row["text"]):
                    counts = counters[split, "sft"]
                    if len(response.encode("utf-8")) > 600:
                        counts[variant + "_excluded_response_bytes"] += 1
                        continue
                    example = tokenizer.response_example(prompt, response)
                    length = len(example["input_ids"])
                    if length > context:
                        counts[variant + "_excluded_context"] += 1
                        continue
                    start = next(
                        i for i, label in enumerate(example["targets"]) if label != -100
                    )
                    full = example["input_ids"] + [example["targets"][-1]]
                    binary, sources = handles[split, "sft"]
                    offset = binary.tell() // 2
                    binary.write(np.asarray(full, dtype="<u2").tobytes())
                    indices[split, "sft"].append((offset, length, start))
                    counts[variant + "_rows"] += 1
                    counts["targets"] += length - start
                    sources.write(
                        json.dumps({"source_id": source, "variant": variant}) + "\n"
                    )
    finally:
        for binary, sources in handles.values():
            binary.close()
            sources.close()
    splits = {}
    for (split, stage), rows in indices.items():
        array = np.asarray(rows, dtype="<i8").reshape(-1, 3)
        array.tofile(destination / f"{split}-{stage}.index.i64")
        if not len(rows):
            raise ValueError(
                "Empty stage; partial preparation retained without manifest"
            )
        splits[f"{split}-{stage}"] = {"rows": len(rows), **counters[split, stage]}
    files = {
        p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)}
        for p in sorted(destination.iterdir())
        if p.is_file()
    }
    manifest = {
        "schema_version": 1,
        "complete": True,
        "corpus_sha256": sha256(corpus),
        "tokenizer_spec": tokenizer.spec,
        "context": context,
        "splits": splits,
        "formats": {"ids": "little-endian uint16", "index": "little-endian int64 Nx3"},
        "long_lm_documents_dropped": 0,
        "state_reset_each_window": True,
        "source_splits_preserved": True,
        "test_tokenized": False,
        "tokenizer_fitted": False,
        "optimizer_updates": 0,
        "source_sha256": source_sha256(__file__),
        "files": files,
    }
    write_json(destination / "manifest.json", manifest)
    return manifest


class TokenDataset:
    def __init__(self, root, split, stage):
        self.root = Path(root)
        self.manifest = read_json(self.root / "manifest.json")
        if self.manifest.get("complete") is not True:
            raise ValueError("Incomplete token corpus")
        key = f"{split}-{stage}"
        info = self.manifest["splits"][key]
        for name in (f"{key}.ids.u16", f"{key}.index.i64"):
            expected = self.manifest["files"][name]
            path = self.root / name
            if (
                path.stat().st_size != expected["bytes"]
                or sha256(path) != expected["sha256"]
            ):
                raise ValueError("Token corpus file differs from manifest")
        self.ids = np.memmap(self.root / f"{key}.ids.u16", mode="r", dtype="<u2")
        self.index = np.memmap(
            self.root / f"{key}.index.i64",
            mode="r",
            dtype="<i8",
            shape=(info["rows"], 3),
        )

    def __len__(self):
        return len(self.index)

    def __getitem__(self, index):
        offset, length, start = map(int, self.index[index])
        ids = self.ids[offset : offset + length + 1].astype(np.int64)
        if len(ids) != length + 1:
            raise ValueError("Truncated token corpus")
        targets = ids[1:].copy()
        targets[:start] = -100
        return {"input_ids": ids[:-1].tolist(), "targets": targets.tolist()}
