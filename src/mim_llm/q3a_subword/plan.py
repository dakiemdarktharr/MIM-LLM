"""Subword post plans with six genuine seed-matched foundation parents.

Creating a plan never authorizes optimization. Seed-zero feasibility parents
cannot be relabelled as three independent foundation initializations.
"""

import math
from pathlib import Path

import torch

from ..foundation.codec import FrozenTokenizer
from ..foundation.plan import load_plan as load_foundation_plan
from ..q3a import data
from ..q3a.io import read_json, read_rows, sha256, signature, source_sha256, write_json
from .foundation_review import check_complete_parent
from .objectives import encode_example, probe_rows


def fingerprints():
    root = Path(__file__).resolve().parents[1]
    paths = list((root / "q3a_subword").glob("*.py")) + list(
        (root / "foundation").glob("*.py")
    )
    paths += [
        root / "models.py",
        root / "training_gate.py",
        root / "q3a/data.py",
        root / "q3a/io.py",
        root / "q3a/objectives.py",
        root / "q3a/runner.py",
        root / "q3a/evaluate.py",
        root / "q3a_reviewed_analysis.py",
    ]
    return {p.relative_to(root).as_posix(): source_sha256(p) for p in sorted(paths)}


def validate_config(config):
    if (
        config["arms"] != ["A0", "A1", "A2", "A3"]
        or config["seeds"] != [0, 1, 2]
        or config["backbones"] != ["mingru", "transformer"]
    ):
        raise ValueError("Require the declared four-arm/two-backbone/three-seed matrix")
    for key in (
        "context",
        "batch_size",
        "post_targets",
        "checkpoint_every_updates",
        "validation_every_updates",
    ):
        if type(config[key]) is not int or config[key] <= 0:
            raise ValueError("Invalid positive post-training setting: " + key)
    if (
        any(
            type(config[k]) not in (int, float) or not math.isfinite(config[k])
            for k in ("learning_rate", "grad_clip", "weight_decay", "js_weight")
        )
        or min(config["learning_rate"], config["grad_clip"]) <= 0
        or min(config["weight_decay"], config["js_weight"]) < 0
    ):
        raise ValueError("Invalid post objective or optimizer setting")
    if (
        config.get("parent_initialization")
        != "independent_foundation_seed_matched_to_post_seed"
    ):
        raise ValueError(
            "A single seed-zero parent does not establish three initialization seeds"
        )
    decoding = config["decoding"]
    if (
        decoding["seeds"] != [17]
        or decoding["max_new_tokens"] != 128
        or decoding["temperature"] != 0.8
        or decoding["top_k"] != 40
    ):
        raise ValueError("Keep the declared fixed subword decoding policy")
    cap = config.get("gpu_hours_cap_per_study")
    if cap is not None and (
        type(cap) not in (int, float) or not math.isfinite(cap) or cap <= 0
    ):
        raise ValueError("Study budget must be finite and positive when supplied")


def dataset_manifest(directory):
    directory = Path(directory)
    manifest = read_json(directory / "manifest.json")
    if (
        signature({k: v for k, v in manifest.items() if k != "dataset_id"})
        != manifest["dataset_id"]
    ):
        raise ValueError("Dataset identity changed")
    if manifest["generator_code_sha256"] != source_sha256(data.__file__):
        raise ValueError("Changed controlled data generator")
    for split in ("train", "validation", "test"):
        if (
            sha256(directory / (split + ".jsonl"))
            != manifest["sha256"][split + ".jsonl"]
        ):
            raise ValueError("Changed dataset split: " + split)
    lock = read_json(directory / "test.lock.json")
    if (
        lock["dataset_id"] != manifest["dataset_id"]
        or lock["sha256"] != manifest["sha256"]["test.jsonl"]
    ):
        raise ValueError("Test integrity lock changed")
    # Test is byte-hashed for integrity, not parsed, tokenized, generated or scored.
    return manifest


def resolve_parents(items, config):
    expected = {(k, s) for k in config["backbones"] for s in config["seeds"]}
    parents, models, common = {}, {}, None
    seen_hashes = set()
    for item in items:
        foundation = load_foundation_plan(item["foundation_plan"])
        run = next((r for r in foundation["runs"] if r["id"] == item["run_id"]), None)
        if run is None or (run["kind"], run["seed"]) not in expected:
            raise ValueError("Wrong foundation parent run/seed")
        key = run["kind"] + "-s" + str(run["seed"])
        path = Path(item["checkpoint"])
        digest = sha256(path)
        if digest in seen_hashes or key in parents:
            raise ValueError("Duplicate/relabelled foundation parent")
        seen_hashes.add(digest)
        verification = read_json(item["verification_receipt"])
        verified = verification["runs"].get(run["id"], {})
        if (
            verification.get("plan_id") != foundation["plan_id"]
            or verified.get("complete") is not True
            or verified.get("per_stage")
            != {s["name"]: s["targets"] for s in foundation["config"]["stages"]}
            or digest
            not in {verified.get("final_sha256"), verified.get("latest_sha256")}
            or not verification.get("archive_sha256")
        ):
            raise ValueError(
                "Parent requires a matching complete per-stage archive audit"
            )
        saved = torch.load(path, map_location="cpu", weights_only=True)
        check_complete_parent(saved, foundation, run)
        del saved
        info = foundation["models"][run["kind"]]
        if info["config"]["context"] != config["context"]:
            raise ValueError("Foundation/post context mismatch")
        if run["kind"] in models and info != models[run["kind"]]:
            raise ValueError("Backbone configuration/count differs between seeds")
        models[run["kind"]] = info
        compatibility = {
            "tokenizer_spec": foundation["tokenizer_spec"],
            "corpus_sha256": foundation["corpus_sha256"],
            "stages": foundation["config"]["stages"],
        }
        if common is not None and compatibility != {
            k: common[k] for k in compatibility
        }:
            raise ValueError(
                "Foundation corpus/tokenizer/schedules differ across seeds"
            )
        if common is None:
            common = {**compatibility, "tokenizer": foundation["tokenizer"]}
        parents[key] = {
            "foundation_plan": str(item["foundation_plan"]),
            "foundation_plan_sha256": sha256(item["foundation_plan"]),
            "foundation_plan_id": foundation["plan_id"],
            "run": run,
            "checkpoint": str(path),
            "checkpoint_sha256": digest,
            "verification_receipt": str(item["verification_receipt"]),
            "verification_receipt_sha256": sha256(item["verification_receipt"]),
            "verified_archive_sha256": verification["archive_sha256"],
        }
    if {(p["run"]["kind"], p["run"]["seed"]) for p in parents.values()} != expected:
        raise ValueError(
            "Need all six genuine completed seed-matched foundation parents"
        )
    return parents, models, common


def checked_writing_gate(path, parents):
    value = read_json(path)
    expected = {
        p["run"]["id"]: p["checkpoint_sha256"]
        for p in parents.values()
        if p["run"]["seed"] == 0
    }
    if (
        value.get("status") != "reviewed_writing_feasibility_passed"
        or not value.get("evidence")
        or not value.get("decision_reason")
        or value.get("foundation_checkpoint_sha256") != expected
    ):
        raise ValueError(
            "Writing feasibility requires reviewed evidence bound to both seed-zero parents"
        )
    for evidence in value["evidence"]:
        if sha256(evidence["path"]) != evidence["sha256"]:
            raise ValueError("Changed writing evidence")
    return {"path": str(path), "sha256": sha256(path)}


def make_plan(config_path, data_dir, parents_path, output, *, writing_gate=None):
    config = read_json(config_path)
    validate_config(config)
    manifest = dataset_manifest(data_dir)
    parents, models, common = resolve_parents(read_json(parents_path), config)
    tokenizer = FrozenTokenizer(common["tokenizer"], common["tokenizer_spec"])
    max_context = 0
    for split in ("train", "validation"):
        rows = read_rows(Path(data_dir) / (split + ".jsonl"))
        if len(rows) != manifest["counts"][split]:
            raise ValueError("Split row count mismatch")
        for bundle in rows:
            data.validate_bundle(bundle)
            for scenario in bundle["scenarios"].values():
                encoded = encode_example(
                    tokenizer,
                    scenario["prompt"],
                    scenario["reference"],
                    config["context"],
                )
                n = max(
                    len(encoded["input_ids"]),
                    len(tokenizer.encode(scenario["prompt"], bos=True))
                    + config["decoding"]["max_new_tokens"],
                )
                if n > config["context"]:
                    raise ValueError("No silent context truncation in a post plan")
                max_context = max(max_context, n)
            for name in (
                "holder",
                "action",
                "cabinet",
                "power_available",
                "permission",
            ):
                probe_rows(tokenizer, bundle, config["context"], name)
    gate = None
    if writing_gate is not None:
        gate = checked_writing_gate(writing_gate, parents)
    value = {
        "schema_version": 1,
        "purpose": "Q3-A subword paired post-training; preparation is not training authorization",
        "config": config,
        "dataset_id": manifest["dataset_id"],
        "data_dir": str(data_dir),
        "data_sha256": manifest["sha256"],
        "models": models,
        "parents": parents,
        "tokenizer": common["tokenizer"],
        "tokenizer_spec": common["tokenizer_spec"],
        "shared_foundation_corpus_sha256": common["corpus_sha256"],
        "foundation_stages": common["stages"],
        "writing_gate": gate,
        "maximum_checked_context": max_context,
        "implementation_fingerprints": fingerprints(),
        "test_locked": True,
        "status": "prepared_training_locked",
        "runs": [
            {
                "id": f"subword-post-{arm}-{kind}-s{seed}",
                "arm": arm,
                "kind": kind,
                "seed": seed,
                "targets": config["post_targets"],
                "parent_key": kind + "-s" + str(seed),
            }
            for kind in config["backbones"]
            for seed in config["seeds"]
            for arm in config["arms"]
        ],
    }
    value["plan_id"] = signature(value)
    write_json(output, value)
    return value


def load_plan(path):
    plan = read_json(path)
    if signature({k: v for k, v in plan.items() if k != "plan_id"}) != plan["plan_id"]:
        raise ValueError("Post plan digest mismatch")
    validate_config(plan["config"])
    if plan["implementation_fingerprints"] != fingerprints():
        raise ValueError("Post implementation changed")
    manifest = dataset_manifest(plan["data_dir"])
    if (
        manifest["dataset_id"] != plan["dataset_id"]
        or manifest["sha256"] != plan["data_sha256"]
    ):
        raise ValueError("Post dataset changed")
    if sha256(plan["tokenizer"]) != plan["tokenizer_spec"]["sha256"]:
        raise ValueError("Post tokenizer changed")
    for parent in plan["parents"].values():
        if (
            sha256(parent["checkpoint"]) != parent["checkpoint_sha256"]
            or sha256(parent["foundation_plan"]) != parent["foundation_plan_sha256"]
            or sha256(parent["verification_receipt"])
            != parent["verification_receipt_sha256"]
        ):
            raise ValueError("Post parent changed")
    if (
        plan["writing_gate"] is not None
        and sha256(plan["writing_gate"]["path"]) != plan["writing_gate"]["sha256"]
    ):
        raise ValueError("Writing gate evidence changed")
    if plan["writing_gate"] is not None:
        checked_writing_gate(plan["writing_gate"]["path"], plan["parents"])
    return plan
