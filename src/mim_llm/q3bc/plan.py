"""Immutable B/C plans bind one real shared initialization plan, not new warm-ups."""

from __future__ import annotations

from pathlib import Path

from ..q3a.io import read_json, read_rows, sha256, signature, source_sha256, write_json
from ..q3a.plan import load_plan as load_shared_plan
from ..tokenizer import ByteTokenizer
from .data import verify


def fingerprints():
    root = Path(__file__).resolve().parents[1]
    files = (
        list((root / "q3bc").glob("*.py"))
        + list((root / "q3a").glob("*.py"))
        + [
            root / n
            for n in (
                "models.py",
                "tokenizer.py",
                "generate.py",
                "training_gate.py",
                "shared_data.py",
            )
        ]
    )
    return {p.relative_to(root).as_posix(): source_sha256(p) for p in sorted(files)}


def make_plan(study, config, data_dir, shared_plan, output):
    c = read_json(config)
    shared = load_shared_plan(shared_plan)
    data = verify(data_dir)
    if study not in ("b", "c") or data["study"] != study or c["study"] != study:
        raise ValueError("Wrong study/config/data")
    for key in (
        "backbones",
        "seeds",
        "tokenizer",
        "context",
        "layers",
        "dropout",
        "batch_size",
        "learning_rate",
        "weight_decay",
        "grad_clip",
        "post_targets",
    ):
        if c[key] != shared["config"][key]:
            raise ValueError(f"Fair shared contract mismatch: {key}")
    expected = [f"{study.upper()}{i}" for i in range(4)]
    if c["arms"] != expected:
        raise ValueError("Four declared conditions required")
    runs = [
        {
            "id": f"{arm}-{kind}-s{seed}",
            "phase": "post",
            "kind": kind,
            "seed": seed,
            "arm": arm,
            "targets": c["post_targets"],
            "parent": f"warmup-{kind}-s{seed}",
        }
        for kind in c["backbones"]
        for seed in c["seeds"]
        for arm in c["arms"]
    ]
    token = ByteTokenizer()
    maximum = 0
    for split in ("train", "validation", "test"):
        for row in read_rows(Path(data_dir) / f"{split}.jsonl"):
            if study == "b":
                length = (
                    len(token.encode(row["prompt"], bos=True))
                    + c["decoding"]["max_new_tokens"]
                )
            else:
                length = (
                    len(token.encode(row["prompt"], bos=True))
                    + c["decoding"]["first_tokens"]
                    + len(token.encode(row["followup"]))
                    + c["decoding"]["max_new_tokens"]
                )
            maximum = max(maximum, length)
    if maximum > c["context"]:
        raise ValueError(f"Task needs {maximum} context, not {c['context']}")
    value = {
        "study": study,
        "config": c,
        "data_dir": Path(data_dir).as_posix(),
        "dataset_id": data["dataset_id"],
        "shared_plan": Path(shared_plan).as_posix(),
        "shared_plan_id": shared["plan_id"],
        "models": shared["models"],
        "runs": runs,
        "maximum_task_context": maximum,
        "implementation_fingerprints": fingerprints(),
        "budget": {
            "post_runs": 24,
            "post_targets": 24 * c["post_targets"],
            "selection_reserve_targets": int(24 * c["post_targets"] * 0.15),
            "warmup_physical_targets_new": 0,
            "shared_initialization_dependency_targets": shared["budget"][
                "unique_warmup_targets"
            ],
        },
        "sealed_bank": None,
        "sealed_bank_id": None,
        "status": "training_locked; bank deferred until real warm-up"
        if study == "c"
        else "training_locked",
    }
    value["plan_id"] = signature(value)
    write_json(output, value)
    return value


def load_plan(path, *, require_bank=False):
    p = read_json(path)
    check = dict(p)
    expected = check.pop("plan_id")
    if signature(check) != expected:
        raise ValueError("Plan modified")
    if verify(p["data_dir"])["dataset_id"] != p["dataset_id"]:
        raise ValueError("Wrong data")
    if load_shared_plan(p["shared_plan"])["plan_id"] != p["shared_plan_id"]:
        raise ValueError("Shared initialization changed")
    if fingerprints() != p["implementation_fingerprints"]:
        raise ValueError("Implementation changed; prepare new plan")
    if p["sealed_bank"]:
        m = read_json(Path(p["sealed_bank"]) / "manifest.json")
        z = dict(m)
        bank_id = z.pop("sealed_bank_id")
        if signature(z) != bank_id or bank_id != p["sealed_bank_id"] or not m["ready"]:
            raise ValueError("Bank not sealed/ready")
        if (
            m["shared_plan_id"] != p["shared_plan_id"]
            or m["dataset_id"] != p["dataset_id"]
        ):
            raise ValueError("Wrong bank provenance")
        for name, digest in m["sha256"].items():
            if sha256(Path(p["sealed_bank"]) / name) != digest:
                raise ValueError("Sealed histories changed")
    elif require_bank and p["study"] == "c":
        raise ValueError(
            "C needs a genuine collected and matched initialization-history bank"
        )
    return p


def bind_bank(plan_path, bank_dir, output):
    p = load_plan(plan_path)
    if p["study"] != "c":
        raise ValueError("Only C has a roll-in bank")
    m = read_json(Path(bank_dir) / "manifest.json")
    if not m["ready"] or len(m["sha256"]) != 24:
        raise ValueError("Stop: insufficient matched histories")
    for key, config_key in [
        ("minimum_sources", "minimum_matched_sources"),
        ("max_nll_gap", "max_nll_gap"),
        ("max_length_gap", "max_length_gap"),
    ]:
        if m[key] != p["config"][config_key]:
            raise ValueError("Matching limits differ from the declared plan")
    p.pop("plan_id")
    p["sealed_bank"] = Path(bank_dir).as_posix()
    p["sealed_bank_id"] = m["sealed_bank_id"]
    p["status"] = "bank_bound_training_locked"
    p["plan_id"] = signature(p)
    write_json(output, p)
    load_plan(output, require_bank=True)
    return p


def freeze_selection(plan_path, checkpoints, registration, output, *, rationale):
    import torch

    p = load_plan(plan_path, require_bank=True)
    r = read_json(registration)
    if (
        r.get("plan_id") != p["plan_id"]
        or r.get("primary_contrast") != p["config"]["primary_contrast"]
        or r.get("test_results_used") is not False
    ):
        raise ValueError(
            "Registration must bind this plan and declared contrast before test"
        )
    if (
        not isinstance(r.get("smallest_useful_effect"), (int, float))
        or not 0 < r["smallest_useful_effect"] < 1
    ):
        raise ValueError("Declare useful effect")
    if (
        not isinstance(r.get("gpu_hours_cap_per_study"), (int, float))
        or r["gpu_hours_cap_per_study"] <= 0
    ):
        raise ValueError("Declare measured GPU-hour cap")
    sample = r.get("test_source_ids", [])
    available = {x["source_id"] for x in read_rows(Path(p["data_dir"]) / "test.jsonl")}
    if (
        not sample
        or len(set(sample)) != len(sample)
        or not set(sample) <= available
        or not rationale.strip()
    ):
        raise ValueError("Declare a complete-source sample and rationale")
    hashes = {}
    ids = set()
    for path in checkpoints:
        c = torch.load(path, map_location="cpu", weights_only=True)
        if c["plan_id"] != p["plan_id"] or not c["complete"] or c["run"]["id"] in ids:
            raise ValueError("Wrong/incomplete/duplicate checkpoint")
        ids.add(c["run"]["id"])
        hashes[Path(path).as_posix()] = sha256(path)
    if ids != {x["id"] for x in p["runs"]}:
        raise ValueError("All 24 declared runs required for final test release")
    write_json(
        output,
        {
            "plan_id": p["plan_id"],
            "dataset_id": p["dataset_id"],
            "checkpoints": hashes,
            "registration": r,
            "registration_sha256": sha256(registration),
            "decoding": p["config"]["decoding"],
            "selection_frozen": True,
            "validation_rationale": rationale,
        },
    )
