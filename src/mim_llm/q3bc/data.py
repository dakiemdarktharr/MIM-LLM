"""Source-disjoint executable worlds for B and C; no invented model outputs."""

from __future__ import annotations

import random
from pathlib import Path

from ..q3a.io import (
    read_json,
    read_rows,
    sha256,
    signature,
    source_sha256,
    write_json,
    write_rows,
)

PLACES = ("shelf", "chest", "table", "bench", "crate", "stand")
STORES = ("drawer", "basket", "cupboard")
NAMES = ("Lan", "Mai", "Huy", "An", "Binh", "Chi")


def b_source(source_id, split, seed, index, lag=256, writes=6):
    rng = random.Random(f"{seed}/{source_id}")
    place = rng.choice(PLACES)
    other = rng.choice([x for x in PLACES if x != place])
    subject = rng.choice(("red key", "tan key", "old key"))
    text = f"{rng.choice(NAMES)} recorded deliveries. The {subject} was first on the {other}. "
    positions = {
        item: rng.choice(PLACES) for item in ("blue coin", "gray card", "pink ball")
    }
    initial_positions = dict(positions)
    text += (
        " ".join(f"The {item} was on the {loc}." for item, loc in positions.items())
        + " "
    )
    windows = {}
    order = ("low", "high") if index % 2 == 0 else ("high", "low")
    events = []
    for window in order:
        text += (
            f"The {subject} moved to the {other}. The {subject} moved to the {place}. "
        )
        evidence = len(text.encode())
        block = ""
        if window == "high":
            for j in range(writes):
                item = ("blue coin", "gray card", "pink ball")[j % 3]
                dest = rng.choice([p for p in PLACES if p != positions[item]])
                positions[item] = dest
                sentence = f"The {item} moved to the {dest}. "
                events.append({"object": item, "location": dest, "window": window})
                block += sentence
        filler = "Rain fell softly outside. "
        if len(block.encode()) > lag:
            raise ValueError("Write block exceeds matched lag")
        while len((block + filler).encode()) <= lag:
            block += filler
        block += " " * (lag - len(block.encode()))
        text += block
        windows[window] = {
            "evidence_end": evidence,
            "probe_end": len(text.encode()),
            "token_delay": lag,
            "semantic_writes": 0 if window == "low" else writes,
        }
    continuation_text = text.encode()[: windows["high"]["probe_end"]].decode()
    prompt = (
        continuation_text
        + "\nThese records contain every move of the target up to this cut point. Continue in three to five natural sentences. State where the "
        + subject
        + " was at the end of these records and explain why later deliveries did not change that location. Additional coherent details are allowed.\nContinuation:\n"
    )
    ref = f"The {subject} was on the {place} at the end of the records. Its latest recorded move had put it there. The deliveries of other objects had not moved it."
    row = {
        "source_id": source_id,
        "split": split,
        "origin": "project-controlled-template",
        "event_text": text,
        "continuation_cut": windows["high"]["probe_end"],
        "subject": subject,
        "answer": place,
        "windows": windows,
        "events": events,
        "initial_other_locations": initial_positions,
        "lag": lag,
        "writes": writes,
        "prompt": prompt,
        "reference": ref,
        "mandatory": {
            "location": place,
            "latest_update": "use_latest_target_update",
            "retention": "other_object_updates_do_not_move_target",
        },
        "position_order": order,
    }
    validate_b(row)
    return row


def validate_b(row):
    positions = dict(row["initial_other_locations"])
    for event in row["events"]:
        if positions[event["object"]] == event["location"]:
            raise ValueError("No-op counted as a semantic write")
        positions[event["object"]] = event["location"]
    for name, w in row["windows"].items():
        if w["probe_end"] - w["evidence_end"] != row["lag"]:
            raise ValueError("Token delay not matched")
        if w["semantic_writes"] != (0 if name == "low" else row["writes"]):
            raise ValueError("Write count mismatch")
        prefix = row["event_text"].encode()[: w["probe_end"]].decode()
        import re

        locations = re.findall(
            r"The " + re.escape(row["subject"]) + r" moved to the (\w+)\.", prefix
        )
        if not locations or locations[-1] != row["answer"]:
            raise ValueError("Probe label is not latest valid target state")


def b_probe(row, arm, index):
    if arm not in ("B0", "B1", "B2", "B3"):
        raise ValueError("Unknown B schedule")
    if arm == "B0":
        window = ("low", "high")[(index // 2) % 2]
        end = row["windows"][window]["evidence_end"]
    else:
        window = (
            "low"
            if arm == "B1"
            else "high"
            if arm == "B2"
            else ("low", "high")[(index // 2) % 2]
        )
        end = row["windows"][window]["probe_end"]
    prefix = row["event_text"].encode()[:end].decode()
    return {
        "prompt": prefix
        + "\nQuestion: Where is the "
        + row["subject"]
        + " now?\nAnswer: ",
        "reference": row["answer"],
        "window": window,
        "prefix_bytes": end,
        "token_delay": end - row["windows"][window]["evidence_end"],
        "semantic_writes": 0
        if arm == "B0"
        else row["windows"][window]["semantic_writes"],
    }


def c_source(source_id, split, seed, index):
    rng = random.Random(f"{seed}/{source_id}")
    holder = rng.choice(NAMES)
    object_name = rng.choice(("brass key", "silver key", "copper key"))
    style = {"train": 0, "validation": 1, "test": 2}[split]
    setup = f"The scene took place in a {rng.choice(('quiet room', 'small office', 'bright hall', 'old kitchen', 'music room', 'reading room'))} at {rng.randrange(7, 19):02d}:00. {holder} held a {object_name}. "
    for _ in range(1 + index % 5):
        prior = holder
        holder = rng.choice([n for n in NAMES if n != prior])
        setup += [
            f"{prior} handed the key to {holder}. ",
            f"{holder} received the key from {prior}. ",
            f"The key passed from {prior} to {holder}. ",
        ][style]
    prompt = (
        setup
        + "Every completed handover happened before this scene. No storage location for the key has been chosen yet. Continue with three natural sentences in which "
        + holder
        + " puts the key in a place and remembers where it is.\nContinuation:\n"
    )
    return {
        "source_id": source_id,
        "split": split,
        "origin": "project-controlled-template",
        "holder": holder,
        "object": object_name,
        "prompt": prompt,
        "followup": "\nLater, a friend asks where to find the key. Continue in three to five sentences, following the events actually written above.\nContinuation:\n",
        "teacher_place": STORES[index % 3],
        "teacher_style": index % 3,
    }


def history_options(row):
    h = row["holder"]
    out = []
    for place in STORES:
        texts = [
            f"{h} put the key in the {place}. The key stayed in the {place}. {h} remembered that place.",
            f"{h} placed the key in the {place}. The key was in the {place}. {h} could find it there.",
            f"{h} stored the key in the {place}. The key remained in the {place}. {h} knew where it was.",
        ]
        for style, text in enumerate(texts):
            out.append({"text": text, "place": place, "style": style})
    return out


def parse_controlled_history(row, text):
    matches = [x for x in history_options(row) if x["text"] == text]
    return matches[0] if len(matches) == 1 else None


def c_suffix(row, place):
    h = row["holder"]
    return f"{h} told the friend to look in the {place}. The key was still there because nobody had moved it. The friend went to that place to find it."


def prepare(
    study,
    output,
    *,
    train_sources=None,
    validation_sources=None,
    test_sources=None,
    seed=2026,
):
    if study not in ("b", "c"):
        raise ValueError("Choose b or c")
    counts = {
        "train": train_sources
        if train_sources is not None
        else (6000 if study == "b" else 600),
        "validation": validation_sources
        if validation_sources is not None
        else (400 if study == "b" else 60),
        "test": test_sources
        if test_sources is not None
        else (400 if study == "b" else 120),
    }
    if min(counts.values()) < 1:
        raise ValueError("Nonempty splits required")
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    hashes = {}
    seen_texts = set()
    rejections = 0
    for split, count in counts.items():
        rows = []
        for i in range(count):
            attempt = 0
            while True:
                kw = (
                    {"lag": (256, 384)[(i // 3) % 2], "writes": (0, 3, 6)[i % 3]}
                    if study == "b" and split != "train"
                    else {}
                )
                row = (b_source if study == "b" else c_source)(
                    f"q3{study}-{split}-{i:06d}", split, f"{seed}/{attempt}", i, **kw
                )
                key = signature(row.get("event_text", row["prompt"]))
                if key not in seen_texts:
                    break
                attempt += 1
                rejections += 1
                if attempt > 1000:
                    raise ValueError("Unique source space exhausted")
            seen_texts.add(key)
            rows.append(row)
        path = output / f"{split}.jsonl"
        write_rows(path, rows)
        hashes[path.name] = sha256(path)
    manifest = {
        "study": study,
        "counts": counts,
        "seed": seed,
        "sha256": hashes,
        "duplicate_draws_rejected": rejections,
        "generator_sha256": source_sha256(__file__),
        "origin": "controlled synthetic, not human-authored",
        "model_history_bank_created": False,
        "b_lag_tokens": 256 if study == "b" else None,
        "c_bank_mode": "constrained token-by-token roll-ins; free-run evaluation"
        if study == "c"
        else None,
    }
    manifest["dataset_id"] = signature(manifest)
    write_json(output / "manifest.json", manifest)
    write_json(
        output / "test.lock.json",
        {
            "dataset_id": manifest["dataset_id"],
            "sha256": hashes["test.jsonl"],
            "purpose": "integrity only",
        },
    )
    return manifest


def verify(directory):
    directory = Path(directory)
    m = read_json(directory / "manifest.json")
    check = dict(m)
    identity = check.pop("dataset_id")
    if signature(check) != identity:
        raise ValueError("Dataset manifest modified")
    lock = read_json(directory / "test.lock.json")
    if lock["dataset_id"] != identity or lock["sha256"] != m["sha256"]["test.jsonl"]:
        raise ValueError("Test integrity changed")
    seen = set()
    for split, n in m["counts"].items():
        path = directory / f"{split}.jsonl"
        if sha256(path) != m["sha256"][path.name]:
            raise ValueError("Data changed")
        rows = read_rows(path)
        if len(rows) != n:
            raise ValueError("Count mismatch")
        for row in rows:
            if row["source_id"] in seen or row["split"] != split:
                raise ValueError("Source leakage")
            seen.add(row["source_id"])
            if m["study"] == "b":
                validate_b(row)
    return m
