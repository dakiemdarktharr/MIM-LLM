"""Generation records and human-judgment aggregation.

Automatic lexical checks are diagnostic only. Paper-level logical validity
requires a verified scoring protocol and blind human judgments.
"""

from __future__ import annotations

import json
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from .generate import generate, generate_from_ids
from .train import file_sha256, load_checkpoint, load_checkpoint_tokenizer


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def lock_benchmark(benchmark: str, lock_file: str) -> dict[str, Any]:
    rows = read_jsonl(benchmark)
    ids = [row["id"] for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate benchmark IDs")
    pairs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    source_splits: dict[str, str] = {}
    for row in rows:
        required = (
            "id",
            "pair_id",
            "source_id",
            "split",
            "prompt",
            "condition_id",
            "changed_span",
            "required_changed_predicates",
            "facts_preserved",
            "actual_obligations",
            "counterfactual_obligations",
            "origin",
        )
        if any(field not in row for field in required):
            raise ValueError(
                f"Benchmark row is missing a required field: {row.get('id')}"
            )
        if row["split"] not in {"train", "validation", "test"}:
            raise ValueError("Invalid benchmark split")
        source_id = row["source_id"]
        if source_id in source_splits and source_splits[source_id] != row["split"]:
            raise ValueError("Source story crosses benchmark splits")
        source_splits[source_id] = row["split"]
        pairs[row["pair_id"]].append(row)
    if any(
        len(pair) != 2 or {row["condition_id"] for row in pair} != {"base", "perturbed"}
        for pair in pairs.values()
    ):
        raise ValueError("Every pair needs base and perturbed conditions")
    for pair in pairs.values():
        base = next(row for row in pair if row["condition_id"] == "base")
        perturbed = next(row for row in pair if row["condition_id"] == "perturbed")
        changed = base["changed_span"]
        if (
            not isinstance(changed, dict)
            or not changed.get("base")
            or not changed.get("perturbed")
            or changed != perturbed["changed_span"]
        ):
            raise ValueError("Pair needs one documented changed span")
        if base["prompt"].count(changed["base"]) != 1:
            raise ValueError("Changed span must occur exactly once in base prompt")
        if (
            base["prompt"].replace(changed["base"], changed["perturbed"])
            != perturbed["prompt"]
            or base["facts_preserved"] != perturbed["facts_preserved"]
            or base["split"] != perturbed["split"]
            or base["source_id"] != perturbed["source_id"]
        ):
            raise ValueError(
                "Pair differs beyond its declared span or changes preserved facts/split"
            )
        required_changes = base["required_changed_predicates"]
        if (
            not required_changes
            or required_changes != perturbed["required_changed_predicates"]
        ):
            raise ValueError("Pair needs shared required-changed predicates")
        base_facts = {
            fact["predicate"]: fact["value"] for fact in base["actual_obligations"]
        }
        changed_facts = {
            fact["predicate"]: fact["value"] for fact in perturbed["actual_obligations"]
        }
        if any(
            predicate not in base_facts
            or predicate not in changed_facts
            or base_facts[predicate] == changed_facts[predicate]
            for predicate in required_changes
        ):
            raise ValueError("A required-changed predicate does not change value")
    lock = {
        "benchmark_sha256": file_sha256(benchmark),
        "examples": len(rows),
        "pairs": len(pairs),
        "splits": {
            split: sum(row["split"] == split for row in rows)
            for split in ("train", "validation", "test")
        },
        "protocol": "paired-story-v1",
    }
    path = Path(lock_file)
    if path.exists() and json.loads(path.read_text(encoding="utf-8")) != lock:
        raise ValueError("Lock file already exists for different benchmark contents")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    return lock


def run_generations(
    checkpoint: str,
    benchmark: str,
    output: str,
    *,
    seed: int = 0,
    max_new_tokens: int = 200,
    temperature: float = 0.8,
    top_k: int = 40,
    self_events: bool = False,
    device: str = "auto",
    split: str = "test",
    lock_file: str | None = None,
) -> None:
    if split not in {"train", "validation", "test", "all"}:
        raise ValueError("Unknown benchmark split")
    if split in {"test", "all"} and lock_file is None:
        raise ValueError("Test generation requires --lock-file")
    checksum = file_sha256(benchmark)
    if lock_file is not None:
        lock = json.loads(Path(lock_file).read_text(encoding="utf-8"))
        if lock.get("benchmark_sha256") != checksum:
            raise ValueError("Benchmark changed after lock")
        if lock.get("protocol") != "paired-story-v1":
            raise ValueError("Benchmark lock uses an older schema; lock it again")
    model, saved = load_checkpoint(checkpoint, device=device)
    system_id = f"{model.config.kind}-train{saved['seed']}-decode{seed}-{file_sha256(checkpoint)[:10]}"
    tokenizer = load_checkpoint_tokenizer(checkpoint, saved)
    actual_device = next(model.parameters()).device
    rows = []
    selected = [
        row for row in read_jsonl(benchmark) if split == "all" or row["split"] == split
    ]
    if not selected:
        raise ValueError(f"No examples in split {split}")
    required = {
        "id",
        "pair_id",
        "source_id",
        "prompt",
        "facts_preserved",
        "actual_obligations",
        "counterfactual_obligations",
        "required_changed_predicates",
        "changed_span",
    }
    if any(not required <= item.keys() for item in selected):
        raise ValueError("Benchmark rows do not match paired-story-v1 schema")
    if model.config.kind == "transformer":
        extra = (
            len(
                tokenizer.encode(
                    "\nContinue the scene, preserving every event already described.\n"
                )
            )
            if self_events
            else 0
        )
        needed = max(
            len(tokenizer.encode(item["prompt"], bos=True))
            + max_new_tokens * (2 if self_events else 1)
            + extra
            for item in selected
        )
        if needed > model.config.context:
            raise ValueError(
                f"Transformer context {model.config.context} is too short for the worst-case evaluation length {needed}"
            )
    for item in selected:
        first = generate(
            model,
            tokenizer,
            item["prompt"],
            seed=seed,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            device=actual_device,
        )
        record = {
            "id": item["id"],
            "pair_id": item["pair_id"],
            "source_id": item["source_id"],
            "prompt": item["prompt"],
            "continuation": first["continuation"],
            "continuation_token_ids": first["token_ids"],
            "valid_utf8": first["valid_utf8"],
            "model_kind": model.config.kind,
            "train_seed": saved["seed"],
            "system_id": system_id,
            "decode_seed": seed,
            "checkpoint": str(checkpoint),
            "benchmark_sha256": checksum,
            "benchmark_split": split,
            "decoding": {
                "temperature": temperature,
                "top_k": top_k,
                "max_new_tokens": max_new_tokens,
            },
            "obligations": {
                key: item[key]
                for key in (
                    "facts_preserved",
                    "actual_obligations",
                    "counterfactual_obligations",
                    "required_changed_predicates",
                    "changed_span",
                )
            },
        }
        if self_events:
            # The first continuation is fixed verbatim, even if it contains a
            # model error. The second task is judged against that actual text.
            instruction = (
                "\nContinue the scene, preserving every event already described.\n"
            )
            followup_ids = (
                tokenizer.encode(item["prompt"], bos=True)
                + first["token_ids"]
                + tokenizer.encode(instruction)
            )
            second = generate_from_ids(
                model,
                tokenizer,
                followup_ids,
                seed=seed + 1,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                device=actual_device,
            )
            record["self_event_followup_prompt_display"] = (
                item["prompt"] + first["continuation"] + instruction
            )
            record["self_event_followup_token_ids"] = followup_ids
            record["self_event_continuation"] = second["continuation"]
            record["self_event_valid_utf8"] = second["valid_utf8"]
        rows.append(record)
    if Path(output).exists():
        raise FileExistsError(f"Generation output already exists: {output}")
    write_jsonl(output, rows)


def make_blind_packet(
    generation_paths: list[str], output: str, key_output: str, *, seed: int = 0
) -> None:
    if len(generation_paths) < 2:
        raise ValueError("Blind comparison requires at least two systems")
    rng = random.Random(seed)
    packet, key = [], []
    seen: set[tuple[str, str]] = set()
    for path in generation_paths:
        for row in read_jsonl(path):
            unique = (str(path), row["id"])
            if unique in seen:
                raise ValueError(f"Duplicate generation {unique}")
            seen.add(unique)
            anonymous = f"sample-{len(packet):06d}"
            packet.append(
                {
                    "anonymous_id": anonymous,
                    "pair_id": row["pair_id"],
                    "prompt": row["prompt"],
                    "continuation": row["continuation"],
                    "obligations": row["obligations"],
                    "self_event_continuation": row.get("self_event_continuation"),
                    "self_event_state_after_first": None,
                    "all_required": None,
                    "contradiction": None,
                    "concrete_event": None,
                    "sentence_count_ok": None,
                    "counterfactual_correct": None,
                    "invariant_correct": None,
                    "self_event_consistent": None,
                    "fluency_1_to_5": None,
                    "coverage_0_to_1": None,
                    "error_type": None,
                    "notes": "",
                }
            )
            key.append(
                {
                    "anonymous_id": anonymous,
                    "path": str(path),
                    "id": row["id"],
                    "pair_id": row["pair_id"],
                    "source_id": row["source_id"],
                    "system_id": row.get("system_id", str(Path(path).resolve())),
                }
            )
    # Preserve packet/key correspondence while randomizing system order.
    indices = list(range(len(packet)))
    rng.shuffle(indices)
    write_jsonl(output, [packet[i] for i in indices])
    write_jsonl(key_output, key)


def aggregate_labels(
    labels_path: str, key_path: str, *, bootstrap_draws: int = 2000, seed: int = 0
) -> dict[str, Any]:
    """Cluster bootstrap by source story, using adjudicated labels only."""
    if bootstrap_draws < 100:
        raise ValueError("Use at least 100 bootstrap draws")
    key = {row["anonymous_id"]: row for row in read_jsonl(key_path)}
    by_system: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    used = set()
    for label in read_jsonl(labels_path):
        anonymous = label["anonymous_id"]
        if anonymous in used or anonymous not in key:
            raise ValueError("Duplicate or unknown anonymous_id")
        used.add(anonymous)
        for field in (
            "all_required",
            "contradiction",
            "concrete_event",
            "sentence_count_ok",
            "counterfactual_correct",
            "invariant_correct",
        ):
            if type(label.get(field)) is not bool:
                raise ValueError(f"Missing adjudicated boolean: {field}")
        if (
            label.get("self_event_continuation") is not None
            and type(label.get("self_event_consistent")) is not bool
        ):
            raise ValueError("Missing self_event_consistent adjudication")
        if label.get("self_event_continuation") is not None and not isinstance(
            label.get("self_event_state_after_first"), dict
        ):
            raise ValueError(
                "Record a state table after the generated first continuation"
            )
        fluency, coverage = label.get("fluency_1_to_5"), label.get("coverage_0_to_1")
        if (
            type(fluency) is not int
            or not 1 <= fluency <= 5
            or type(coverage) not in (int, float)
            or not 0 <= coverage <= 1
        ):
            raise ValueError("Invalid fluency or coverage label")
        record = key[anonymous]
        by_system[record["system_id"]][record["source_id"]].append(
            {**label, "pair_id": record["pair_id"]}
        )
    if len(used) != len(key):
        raise ValueError("Incomplete adjudication packet")
    rng = random.Random(seed)
    output: dict[str, Any] = {}
    for system, clusters in by_system.items():
        source_ids = sorted(clusters)

        def stats(
            ids: list[str], clusters: dict[str, list[dict[str, Any]]] = clusters
        ) -> dict[str, float]:
            rows = [item for source_id in ids for item in clusters[source_id]]
            scores = {
                "primary": statistics.mean(
                    float(
                        row["all_required"]
                        and row["sentence_count_ok"]
                        and not row["contradiction"]
                    )
                    for row in rows
                ),
                "coverage": statistics.mean(row["coverage_0_to_1"] for row in rows),
                "contradiction": statistics.mean(
                    float(row["contradiction"]) for row in rows
                ),
                "generic_evasion": statistics.mean(
                    float(not row["concrete_event"]) for row in rows
                ),
                "counterfactual_correct": statistics.mean(
                    float(row["counterfactual_correct"]) for row in rows
                ),
                "invariant_correct": statistics.mean(
                    float(row["invariant_correct"]) for row in rows
                ),
                "fluency": statistics.mean(row["fluency_1_to_5"] for row in rows),
            }
            followed = [
                row for row in rows if row.get("self_event_continuation") is not None
            ]
            if followed:
                scores["self_event_success"] = statistics.mean(
                    float(row["concrete_event"] and row["self_event_consistent"])
                    for row in followed
                )
            pair_results = []
            for source_id in ids:
                pairs: dict[str, list[dict[str, Any]]] = defaultdict(list)
                for row in clusters[source_id]:
                    pairs[row["pair_id"]].append(row)
                pair_results.extend(
                    float(
                        len(pair_rows) == 2
                        and all(
                            row["all_required"]
                            and row["sentence_count_ok"]
                            and not row["contradiction"]
                            and row["invariant_correct"]
                            for row in pair_rows
                        )
                    )
                    for pair_rows in pairs.values()
                )
            scores["pair_success"] = statistics.mean(pair_results)
            return scores

        point = stats(source_ids)
        draws = {metric: [] for metric in point}
        for _ in range(bootstrap_draws):
            selected = rng.choices(source_ids, k=len(source_ids))
            sampled = stats(selected)
            for metric, value in sampled.items():
                draws[metric].append(value)
        ci = {}
        for metric, values in draws.items():
            values.sort()
            ci[metric] = [
                values[int(0.025 * bootstrap_draws)],
                values[min(bootstrap_draws - 1, int(0.975 * bootstrap_draws))],
            ]
        output[system] = {
            "source_stories": len(source_ids),
            "pairs": len(
                {row["pair_id"] for cluster in clusters.values() for row in cluster}
            ),
            "continuations": sum(map(len, clusters.values())),
            "point": point,
            "cluster_bootstrap_95pct": ci,
        }
    return output
