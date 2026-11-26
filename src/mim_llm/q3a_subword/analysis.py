"""Subword provenance with unchanged human primary judgments/source bootstrap.

Two genuine independent readers remain required by this analysis contract.
The currently available author-only feasibility review is a separate activity.
"""

import statistics
from collections import defaultdict
from pathlib import Path

from ..foundation.codec import FrozenTokenizer
from ..q3a.evaluate import analyze, read_labels
from ..q3a.io import read_json, read_rows, sha256, signature, source_sha256
from ..q3a_reviewed_analysis import JOIN_FIELDS, QUALITY_RULE, validate_panel
from .evaluate import read_selection
from .plan import load_plan

VERSION = "q3a-subword-reviewed-quality-1"
PRIMARY_METRIC = "mean_joint_pair_success_effective_and_noop"


def join_generations(plan, key, files):
    for path in files:
        receipt = read_json(str(path) + ".receipt.json")
        if receipt.get("complete") is not True or receipt.get(
            "output_sha256"
        ) != sha256(path):
            raise ValueError("A complete hash-matching generation receipt is required")
    rows = [r for path in files for r in read_rows(path)]
    byid = {r["generation_id"]: r for r in rows}
    if (
        not rows
        or len(byid) != len(rows)
        or len(key) != len(rows)
        or len({r["generation_id"] for r in key}) != len(key)
        or {r["generation_id"] for r in key} != set(byid)
    ):
        raise ValueError("Generations and private key must form an exact unique panel")
    tokenizer = FrozenTokenizer(plan["tokenizer"], plan["tokenizer_spec"])
    known = {r["id"]: r for r in plan["runs"]}
    validity = {}
    for item in key:
        row = byid[item["generation_id"]]
        if (
            any(row[k] != item[k] for k in JOIN_FIELDS)
            or row["plan_id"] != plan["plan_id"]
            or row["run"] != known.get(row["run"]["id"])
        ):
            raise ValueError("Generation plan/run differs from its key")
        identity = signature(
            {
                k: row[k]
                for k in ("scenario_id", "run", "checkpoint_sha256", "decode_seed")
            }
        )
        ids = row["token_ids"]
        if (
            row["generation_id"] != identity
            or row.get("tokenizer_sha256") != plan["tokenizer_spec"]["sha256"]
            or not isinstance(ids, list)
            or any(
                type(t) is not int
                or not 0 <= t < tokenizer.vocab_size
                or t in {tokenizer.bos_id, tokenizer.eos_id, tokenizer.pad_id}
                for t in ids
            )
        ):
            raise ValueError("Raw emitted subword IDs and frozen tokenizer required")
        text = tokenizer.decode(ids)
        clean = "\ufffd" not in text
        if (
            text != row["continuation"]
            or type(row["valid_utf8"]) is not bool
            or row["valid_utf8"] != clean
        ):
            raise ValueError("Generated text differs from unmodified subword decoding")
        validity[item["item_id"]] = clean
    return rows, validity


def verify_sources(plan, generations, split, *, frozen=None):
    bundles = {
        b["source_id"]: b
        for b in read_rows(Path(plan["data_dir"]) / (split + ".jsonl"))
    }
    for row in generations:
        bundle = bundles[row["source_id"]]
        scenario = bundle["scenarios"][row["role"]]
        if (
            row["scenario_id"] != scenario["id"]
            or row["prompt"] != scenario["prompt"]
            or row["world"] != scenario["world"]
            or row["expected_facts"] != scenario["facts"]
            or row["mandatory"] != scenario["mandatory"]
            or row["pairs"] != bundle["pairs"]
            or row["depth"] != bundle["depth"]
        ):
            raise ValueError("Generation no longer matches its source and oracle")
        if (
            frozen
            and row["checkpoint_sha256"]
            != frozen["checkpoints"][row["run"]["id"]]["sha256"]
        ):
            raise ValueError("Generation checkpoint was not frozen for its run")


def reviewed_analyze(
    plan_path,
    labels_a,
    labels_b,
    key_path,
    generation_files,
    *,
    selection=None,
    adjudicated=None,
    draws=2000,
):
    plan = load_plan(plan_path)
    key = read_rows(key_path)
    if not key or {r["split"] for r in key} not in ({"validation"}, {"test"}):
        raise ValueError("Use one held-out split")
    split = key[0]["split"]
    frozen = read_selection(plan, selection) if split == "test" else None
    generations, validity = join_generations(plan, key, generation_files)
    sources = frozen["analysis_registration"]["test_source_ids"] if frozen else None
    panel = validate_panel(
        key,
        seeds=plan["config"]["seeds"] if frozen else None,
        backbones=plan["config"]["backbones"] if frozen else None,
        arms=frozen["analysis_registration"]["test_arms"] if frozen else None,
        decodes=plan["config"]["decoding"]["seeds"],
        sources=sources,
    )
    verify_sources(plan, generations, split, frozen=frozen)
    result = analyze(labels_a, labels_b, key_path, adjudicated=adjudicated, draws=draws)
    result["analysis_provenance"] = {
        "version": VERSION,
        "source_sha256": source_sha256(__file__),
        "primary_analyzer_sha256": source_sha256(
            Path(__file__).parents[1] / "q3a/evaluate.py"
        ),
        "generation_file_sha256": [sha256(p) for p in generation_files],
        "key_sha256": sha256(key_path),
        "label_sha256": [sha256(labels_a), sha256(labels_b)],
        "adjudication_sha256": sha256(adjudicated) if adjudicated else None,
        "quality_aggregation": QUALITY_RULE,
        "primary_definition_changed": False,
        "complete_panel": panel,
        "training_plan_id": plan["plan_id"],
        "selection_sha256": sha256(selection) if frozen else None,
        "text_validity_role": "secondary_writing_metric_human_format_remains_primary",
    }
    if result.get("adjudication_required"):
        return result
    items = {r["item_id"] for r in key}
    a, b = read_labels(labels_a, items), read_labels(labels_b, items)
    final = read_labels(adjudicated, items) if adjudicated else None
    grouped = defaultdict(list)
    for row in key:
        item = row["item_id"]
        grouped[(row["run"]["kind"], row["run"]["arm"], row["run"]["seed"])].append(
            {
                "coverage": final[item]["coverage_fraction"]
                if final
                else statistics.mean(
                    [a[item]["coverage_fraction"], b[item]["coverage_fraction"]]
                ),
                "fluency": final[item]["fluency_1_to_5"]
                if final
                else statistics.mean(
                    [a[item]["fluency_1_to_5"], b[item]["fluency_1_to_5"]]
                ),
                "clean_text": validity[item],
            }
        )
    for summary in result["quality_summaries"]:
        values = grouped[
            (summary["backbone"], summary["arm"], summary["training_seed"])
        ]
        summary.update(
            coverage=statistics.mean(x["coverage"] for x in values),
            fluency=statistics.mean(x["fluency"] for x in values),
            clean_utf8_fraction=statistics.mean(x["clean_text"] for x in values),
            outputs=len(values),
        )
    return result
