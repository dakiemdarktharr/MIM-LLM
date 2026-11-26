"""Versioned analysis corrections without changing the frozen training bundle.

Primary judgments/bootstrap retain the frozen analyzer's definition. This layer
checks a complete source/seed panel, joins original generations, and aggregates
quality from both readers unless explicit adjudication is provided.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from .q3a.evaluate import analyze, read_labels
from .q3a.io import read_json, read_rows, sha256, signature, source_sha256, write_json
from .q3a.plan import load_plan

VERSION = "q3a-reviewed-quality-1"
QUALITY_RULE = "mean_of_two_readers_unless_explicitly_adjudicated"
ROLES = {"base", "effective", "noop"}
JOIN_FIELDS = ("plan_id", "split", "source_id", "role", "run", "decode_seed", "pairs")


def validate_panel(
    key, *, seeds=None, decodes=None, backbones=None, sources=None, arms=None
):
    if not key or len({r["item_id"] for r in key}) != len(key):
        raise ValueError("Empty/duplicate annotation key")
    if len({r["plan_id"] for r in key}) != 1 or len({r["split"] for r in key}) != 1:
        raise ValueError("Do not mix plans or splits")
    seeds = set(seeds if seeds is not None else (r["run"]["seed"] for r in key))
    decodes = set(decodes if decodes is not None else (r["decode_seed"] for r in key))
    backbones = set(
        backbones if backbones is not None else (r["run"]["kind"] for r in key)
    )
    sources = set(sources if sources is not None else (r["source_id"] for r in key))
    arms = set(arms if arms is not None else (r["run"]["arm"] for r in key))
    if not {"A1", "A2"} <= arms or not arms <= {"A0", "A1", "A2", "A3"}:
        raise ValueError("Primary A1/A2 panel required; unknown conditions rejected")
    actual = [
        (
            r["run"]["kind"],
            r["run"]["arm"],
            r["run"]["seed"],
            r["decode_seed"],
            r["source_id"],
            r["role"],
        )
        for r in key
    ]
    expected = set(itertools.product(backbones, arms, seeds, decodes, sources, ROLES))
    if len(set(actual)) != len(actual) or set(actual) != expected:
        raise ValueError(
            "Incomplete/duplicate source-seed panel; keep every declared source, role and seed"
        )
    return {
        "backbones": sorted(backbones),
        "arms": sorted(arms),
        "training_seeds": sorted(seeds),
        "decoding_seeds": sorted(decodes),
        "source_clusters": len(sources),
        "items": len(actual),
    }


def join_generations(key, generation_files):
    rows = [r for path in generation_files for r in read_rows(path)]
    byid = {r["generation_id"]: r for r in rows}
    requested = [r["generation_id"] for r in key]
    if (
        not rows
        or len(byid) != len(rows)
        or len(set(requested)) != len(requested)
        or set(requested) != set(byid)
    ):
        raise ValueError("Generations and private key must form an exact unique panel")
    validity = {}
    for item in key:
        row = byid[item["generation_id"]]
        if any(item[field] != row[field] for field in JOIN_FIELDS):
            raise ValueError("Generation metadata differs from its private key")
        ids = row["token_ids"]
        if not isinstance(ids, list) or any(
            type(x) is not int or not 3 <= x < 259 for x in ids
        ):
            raise ValueError("Raw emitted byte token IDs required")
        raw = bytes(x - 3 for x in ids)
        text = raw.decode("utf-8", errors="replace")
        if text != row["continuation"]:
            raise ValueError("Continuation no longer matches raw generated token IDs")
        clean = "\ufffd" not in text
        if type(row["valid_utf8"]) is not bool or row["valid_utf8"] != clean:
            raise ValueError("Stale/missing generated-text validity flag")
        validity[item["item_id"]] = clean
    return rows, validity


def validate_selection(plan, selection, generations):
    if selection is None:
        raise ValueError("Test analysis locked: frozen selection required")
    c = plan["config"]
    if (
        selection.get("selection_frozen") is not True
        or selection["plan_id"] != plan["plan_id"]
        or selection["dataset_id"] != plan["dataset_id"]
        or selection["decoding"] != c["decoding"]
    ):
        raise ValueError("Wrong frozen selection/decoding")
    reg = selection["analysis_registration"]
    if (
        reg.get("analysis_version") != VERSION
        or reg.get("analysis_source_sha256") != source_sha256(__file__)
        or reg.get("quality_aggregation") != QUALITY_RULE
        or reg.get("complete_source_seed_grid_required") is not True
        or reg.get("text_validity_role")
        != "secondary_writing_metric_human_format_remains_primary"
    ):
        raise ValueError("Register this analysis version/rules before final test")
    if (
        reg.get("plan_id") != plan["plan_id"]
        or reg.get("test_results_used") is not False
        or selection.get("test_results_used") is not False
        or reg.get("primary_contrast") != ["A1", "A2"]
    ):
        raise ValueError("Wrong registration plan/contrast or prior test use")
    effect = reg.get("smallest_useful_effect")
    hours = reg.get("gpu_hours_cap_per_study")
    if (
        type(effect) not in (int, float)
        or not 0 < effect < 1
        or type(hours) not in (int, float)
        or not math.isfinite(hours)
        or hours <= 0
        or not reg.get("sample_method_and_rationale", "").strip()
    ):
        raise ValueError(
            "Useful effect, finite measured cap and sampling rationale required"
        )
    arms = reg.get("test_arms", [])
    if len(set(arms)) != len(arms) or not {"A1", "A2"} <= set(arms) <= {
        "A0",
        "A1",
        "A2",
        "A3",
    }:
        raise ValueError("Predeclare included test arms, including primary A1/A2")
    sources = reg.get("test_source_ids", [])
    if not sources or len(set(sources)) != len(sources):
        raise ValueError("Predeclared complete-source sample required")
    frozen = set(selection["checkpoints"].values())
    if any(r["checkpoint_sha256"] not in frozen for r in generations):
        raise ValueError("Generation checkpoint was not frozen")
    return sources


def reviewed_analyze(
    labels_a,
    labels_b,
    key_path,
    generation_files,
    *,
    adjudicated=None,
    draws=2000,
    seeds=None,
    decodes=None,
    backbones=None,
    sources=None,
    arms=None,
):
    key = read_rows(key_path)
    panel = validate_panel(
        key,
        seeds=seeds,
        decodes=decodes,
        backbones=backbones,
        sources=sources,
        arms=arms,
    )
    _, validity = join_generations(key, generation_files)
    result = analyze(labels_a, labels_b, key_path, adjudicated=adjudicated, draws=draws)
    result["analysis_provenance"] = {
        "version": VERSION,
        "source_sha256": source_sha256(__file__),
        "frozen_primary_analyzer_sha256": source_sha256(
            Path(__file__).parent / "q3a/evaluate.py"
        ),
        "generation_file_sha256": [sha256(p) for p in generation_files],
        "key_sha256": sha256(key_path),
        "label_sha256": [sha256(labels_a), sha256(labels_b)],
        "adjudication_sha256": sha256(adjudicated) if adjudicated else None,
        "quality_aggregation": QUALITY_RULE,
        "text_validity_role": "secondary_writing_metric_human_format_remains_primary",
        "primary_definition_changed": False,
        "complete_panel": panel,
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


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", required=True)
    p.add_argument("--labels-a", required=True)
    p.add_argument("--labels-b", required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--generations", nargs="+", required=True)
    p.add_argument("--selection")
    p.add_argument("--adjudicated")
    p.add_argument("--draws", type=int, default=2000)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    plan = load_plan(args.plan)
    key = read_rows(args.key)
    generations, _ = join_generations(key, args.generations)
    known = {r["id"]: r for r in plan["runs"] if r["phase"] == "post"}
    for row in generations:
        if row["plan_id"] != plan["plan_id"] or row["run"] != known.get(
            row["run"]["id"]
        ):
            raise ValueError("Unknown/wrong training plan or run")
        identifier = signature(
            {
                k: row[k]
                for k in ("scenario_id", "run", "checkpoint_sha256", "decode_seed")
            }
        )
        if row["generation_id"] != identifier:
            raise ValueError("Changed generation identity")
    split = key[0]["split"]
    if split not in {"validation", "test"}:
        raise ValueError("Held-out panels only")
    source_rows = {
        r["source_id"]: r for r in read_rows(Path(plan["data_dir"]) / f"{split}.jsonl")
    }
    for row in generations:
        bundle = source_rows[row["source_id"]]
        scenario = bundle["scenarios"][row["role"]]
        if (
            row["scenario_id"] != scenario["id"]
            or row["world"] != scenario["world"]
            or row["prompt"] != scenario["prompt"]
            or row["mandatory"] != scenario["mandatory"]
            or row["expected_facts"] != scenario["facts"]
            or row["pairs"] != bundle["pairs"]
        ):
            raise ValueError(
                "Generation no longer matches declared source facts/prompt"
            )
    selection = read_json(args.selection) if args.selection else None
    sources = (
        validate_selection(plan, selection, generations) if split == "test" else None
    )
    result = reviewed_analyze(
        args.labels_a,
        args.labels_b,
        args.key,
        args.generations,
        adjudicated=args.adjudicated,
        draws=args.draws,
        seeds=plan["config"]["seeds"] if split == "test" else None,
        decodes=plan["config"]["decoding"]["seeds"],
        backbones=plan["config"]["backbones"] if split == "test" else None,
        sources=sources,
        arms=selection["analysis_registration"]["test_arms"]
        if split == "test"
        else None,
    )
    result["analysis_provenance"].update(
        training_plan_id=plan["plan_id"],
        selection_sha256=sha256(args.selection) if args.selection else None,
        analysis_registration_sha256=selection.get("analysis_registration_sha256")
        if selection
        else None,
    )
    write_json(args.output, result)
    print(
        json.dumps(
            {
                "output": args.output,
                "adjudication_required": result.get("adjudication_required", False),
                "analysis_version": VERSION,
            }
        )
    )


if __name__ == "__main__":
    main()
