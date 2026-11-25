"""Content-addressed plans and runs. Planning never executes a training run."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ..models import ModelConfig
from ..protocol import match_width
from ..tokenizer import ByteTokenizer
from .data import verify_dataset
from .io import read_json, read_rows, sha256, signature, source_sha256, write_json


def implementation_fingerprints():
    root = Path(__file__).resolve().parents[1]
    files = list((root / "q3a").glob("*.py")) + [
        root / n
        for n in (
            "models.py",
            "tokenizer.py",
            "generate.py",
            "training_gate.py",
            "shared_data.py",
        )
    ]
    return {p.relative_to(root).as_posix(): source_sha256(p) for p in sorted(files)}


def validate_config(c):
    if (
        c["arms"] != ["A0", "A1", "A2", "A3"]
        or c["backbones"] != ["mingru", "transformer"]
        or c["seeds"] != [0, 1, 2]
    ):
        raise ValueError(
            "This preregistration draft requires the declared 4x2x3 matrix"
        )
    if c["tokenizer"] != "fixed_utf8_byte_259":
        raise ValueError("Frozen byte tokenizer required")
    if (
        min(
            c["post_targets"],
            c["warmup_targets"],
            c["context"],
            c["batch_size"],
            c["checkpoint_every_updates"],
        )
        < 1
    ):
        raise ValueError("Invalid positive budget/settings")
    if c["learning_rate"] <= 0 or c["grad_clip"] <= 0 or c["js_weight"] < 0:
        raise ValueError("Invalid objective settings")


def make_plan(config_path, data_dir, warmup, output):
    c = read_json(config_path)
    validate_config(c)
    m = verify_dataset(data_dir)
    warmup = Path(warmup)
    rows = read_rows(warmup)
    from ..shared_data import validate_source_groups

    validate_source_groups(rows)
    provenance = read_json(str(warmup) + ".manifest.json")
    if (
        provenance.get("sha256") != sha256(warmup)
        or not provenance.get("license")
        or not provenance.get("revision")
    ):
        raise ValueError("Warm-up requires valid checksum, license and pinned revision")
    if len({r["source_id"] for r in rows}) != len(rows) or len(
        {signature(r["text"]) for r in rows}
    ) != len(rows):
        raise ValueError("Duplicate warmup sources/texts")
    if any(
        r["split"] not in ("train", "validation", "test") or not r["text"].strip()
        for r in rows
    ):
        raise ValueError("Invalid warmup rows")
    if not any(r["split"] == "train" for r in rows) or not any(
        r["split"] == "validation" for r in rows
    ):
        raise ValueError("Warm-up requires train and validation sources")
    source_sets = {
        s: {r["source_id"] for r in rows if r["split"] == s}
        for s in ("train", "validation", "test")
    }
    if any(
        source_sets[a] & source_sets[b]
        for a, b in [("train", "validation"), ("train", "test"), ("validation", "test")]
    ):
        raise ValueError("Warmup source leakage")
    template = ModelConfig(
        vocab_size=259, context=c["context"], layers=c["layers"], dropout=c["dropout"]
    )
    models = {
        kind: match_width(c["target_parameters"], replace(template, kind=kind))
        for kind in c["backbones"]
    }
    if any(abs(x["relative_parameter_gap"]) > 0.02 for x in models.values()):
        raise ValueError("Parameter mismatch")
    lengths = []
    t = ByteTokenizer()
    for split in ("train", "validation", "test"):
        for bundle in read_rows(Path(data_dir) / f"{split}.jsonl"):
            for s in bundle["scenarios"].values():
                n = len(t.encode(s["prompt"], bos=True))
                lengths.append(
                    max(
                        n + len(t.encode(s["reference"], eos=True)) - 1,
                        n + c["decoding"]["max_new_tokens"],
                    )
                )
    if max(lengths) > c["context"]:
        raise ValueError(f"Context too short: need {max(lengths)}")
    runs = []
    for kind in c["backbones"]:
        for seed in c["seeds"]:
            parent = f"warmup-{kind}-s{seed}"
            runs.append(
                {
                    "id": parent,
                    "phase": "warmup",
                    "kind": kind,
                    "seed": seed,
                    "targets": c["warmup_targets"],
                    "parent": None,
                }
            )
            for arm in c["arms"]:
                runs.append(
                    {
                        "id": f"{arm}-{kind}-s{seed}",
                        "phase": "post",
                        "kind": kind,
                        "seed": seed,
                        "arm": arm,
                        "targets": c["post_targets"],
                        "parent": parent,
                    }
                )
    value = {
        "schema_version": 1,
        "config": c,
        "dataset_id": m["dataset_id"],
        "data_dir": Path(data_dir).as_posix(),
        "warmup": warmup.as_posix(),
        "warmup_sha256": sha256(warmup),
        "warmup_manifest_signature": signature(
            read_json(str(warmup) + ".manifest.json")
        )
        if Path(str(warmup) + ".manifest.json").is_file()
        else None,
        "implementation_fingerprints": implementation_fingerprints(),
        "models": models,
        "runs": runs,
        "maximum_task_context": max(lengths),
        "budget": {
            "post_runs": 24,
            "post_targets": 24 * c["post_targets"],
            "shared_warmup_runs": 6,
            "unique_warmup_targets": 6 * c["warmup_targets"],
            "selection_reserve_targets": int(
                24 * c["post_targets"] * c["selection_reserve_fraction"]
            ),
        },
        "measured_train_throughput": None,
        "colab_sku_verified": False,
        "colab_cu_rate": None,
        "status": "prepared_training_locked",
    }
    value["plan_id"] = signature(value)
    write_json(output, value)
    return value


def load_plan(path):
    plan = read_json(path)
    check = dict(plan)
    expected = check.pop("plan_id")
    if signature(check) != expected:
        raise ValueError("Plan hash mismatch")
    validate_config(plan["config"])
    m = verify_dataset(plan["data_dir"])
    if (
        m["dataset_id"] != plan["dataset_id"]
        or sha256(plan["warmup"]) != plan["warmup_sha256"]
    ):
        raise ValueError("Changed input data")
    if (
        plan["warmup_manifest_signature"] is not None
        and signature(read_json(str(plan["warmup"]) + ".manifest.json"))
        != plan["warmup_manifest_signature"]
    ):
        raise ValueError("Changed warmup provenance")
    if plan["implementation_fingerprints"] != implementation_fingerprints():
        raise ValueError("Implementation changed; prepare a new plan before training")
    from ..shared_data import general_rows

    general_rows(plan["warmup"])
    return plan


def freeze_selection(
    plan_path, checkpoint_paths, output, *, rationale, registration=None
):
    import torch

    plan = load_plan(plan_path)
    if not rationale.strip() or not checkpoint_paths:
        raise ValueError("Validation rationale and checkpoints required")
    if registration is None:
        raise ValueError(
            "Freeze the analysis/sample/resource registration before test release"
        )
    reg = read_json(registration)
    effect = reg.get("smallest_useful_effect")
    hours = reg.get("gpu_hours_cap_per_study")
    if (
        reg.get("plan_id") != plan["plan_id"]
        or reg.get("primary_contrast") != ["A1", "A2"]
        or reg.get("test_results_used") is not False
    ):
        raise ValueError("Wrong registration plan/contrast or test already used")
    if (
        not isinstance(effect, (float, int))
        or not 0 < effect < 1
        or not isinstance(hours, (float, int))
        or hours <= 0
    ):
        raise ValueError(
            "Declare a useful effect and measured resource cap before releasing test"
        )
    sample = reg.get("test_source_ids", [])
    available = {
        r["source_id"] for r in read_rows(Path(plan["data_dir"]) / "test.jsonl")
    }
    if (
        not sample
        or len(set(sample)) != len(sample)
        or not set(sample) <= available
        or not reg.get("sample_method_and_rationale", "").strip()
    ):
        raise ValueError("Predeclare a valid complete-source sample")
    checkpoints = {Path(p).as_posix(): sha256(p) for p in checkpoint_paths}
    run_ids = set()
    for path in checkpoint_paths:
        ckpt = torch.load(path, map_location="cpu", weights_only=True)
        if (
            ckpt["plan_id"] != plan["plan_id"]
            or not ckpt["complete"]
            or ckpt["run"]["phase"] != "post"
        ):
            raise ValueError(
                "Freeze only complete post-training checkpoints from this plan"
            )
        if ckpt["run"]["id"] in run_ids:
            raise ValueError("Duplicate run in selection")
        run_ids.add(ckpt["run"]["id"])
    if run_ids != {r["id"] for r in plan["runs"] if r["phase"] == "post"}:
        raise ValueError(
            "Complete the declared 24-run panel before releasing its final test"
        )
    write_json(
        output,
        {
            "plan_id": plan["plan_id"],
            "dataset_id": plan["dataset_id"],
            "checkpoints": checkpoints,
            "decoding": plan["config"]["decoding"],
            "validation_rationale": rationale,
            "selection_frozen": True,
            "test_results_used": False,
            "analysis_registration": reg,
            "analysis_registration_sha256": sha256(registration),
        },
    )
