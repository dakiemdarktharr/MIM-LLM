"""Prepare/verify three studies without fitting a tokenizer or updating weights."""

from __future__ import annotations

import argparse
from pathlib import Path

from mim_llm.q3a.data import prepare as prepare_a
from mim_llm.q3a.io import read_json, sha256, write_json
from mim_llm.q3a.plan import load_plan as load_a
from mim_llm.q3a.plan import make_plan as make_a
from mim_llm.q3a.preflight import preflight as check_a
from mim_llm.q3bc.data import prepare as prepare_bc
from mim_llm.q3bc.plan import load_plan, make_plan
from mim_llm.q3bc.preflight import preflight


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/three-q3-final-20261126")
    parser.add_argument("--data-root", default="data/processed/three-q3-final-reviewed")
    parser.add_argument(
        "--warmup", default="data/processed/three-q3-shared-warmup.jsonl"
    )
    parser.add_argument("--original-warmup", default="data/raw/q3a-tinystories.jsonl")
    parser.add_argument("--check-devices", default="cpu")
    args = parser.parse_args()
    root = Path(args.output)
    data_root = Path(args.data_root)
    if not Path(args.warmup).is_file():
        from mim_llm.shared_data import prepare_format_warmup

        if not Path(args.original_warmup).is_file():
            raise FileNotFoundError(
                "Fetch the pinned TinyStories subset or use the bundle first"
            )
        prepare_format_warmup(args.original_warmup, args.warmup)
    root.mkdir(parents=True, exist_ok=True)
    devices = args.check_devices.split(",")
    plans = {}
    objects = {}
    for study in ("a", "b", "c"):
        data = data_root / study
        folder = root / study
        folder.mkdir(exist_ok=True)
        if not data.exists():
            (prepare_a(data) if study == "a" else prepare_bc(study, data))
        file = folder / "plan.json"
        if file.exists():
            p = load_a(file) if study == "a" else load_plan(file)
        elif study == "a":
            p = make_a("configs/q3a/pilot.json", data, args.warmup, file)
        else:
            p = make_plan(
                study, f"configs/q3{study}/pilot.json", data, plans["a"], file
            )
        plans[study] = file.as_posix()
        objects[study] = p
        for device in devices:
            receipt = folder / f"preflight-{device}.json"
            if not receipt.exists():
                (
                    check_a(file, receipt, device=device)
                    if study == "a"
                    else preflight(file, receipt, device=device)
                )
        snapshot = {
            "status": "prepared_training_locked",
            "study": study,
            "plan_path": file.as_posix(),
            "plan_id": p["plan_id"],
            "dataset_manifest": read_json(data / "manifest.json"),
            "models": p["models"],
            "maximum_task_context": p["maximum_task_context"],
            "budget": p["budget"],
            "shared_warmup_plan": plans["a"],
            "shared_warmup_manifest": read_json(str(args.warmup) + ".manifest.json"),
            "production_model_history_bank_created": False,
            "optimizer_steps": 0,
            "model_training_authorized": False,
            "tokenizer_fitted": False,
        }
        write_json(
            Path(f"configs/q3{study}") / "prepared_snapshot.json",
            snapshot,
            replace=True,
        )
    graph = [
        {"id": r["id"], "phase": "warmup", "plan": plans["a"], "depends_on": []}
        for r in objects["a"]["runs"]
        if r["phase"] == "warmup"
    ]
    for kind in ("mingru", "transformer"):
        for seed in (0, 1, 2):
            for arm_index in range(4):
                for study in ("a", "b", "c"):
                    identifier = f"{study.upper()}{arm_index}-{kind}-s{seed}"
                    graph.append(
                        {
                            "id": identifier,
                            "phase": "post",
                            "plan": plans[study],
                            "depends_on": [f"warmup-{kind}-s{seed}"]
                            + (["C-bank-collected-and-sealed"] if study == "c" else []),
                        }
                    )
    registry = {
        "plans": plans,
        "shared_warmup_plan": plans["a"],
        "training_authorized": False,
        "job_graph": graph,
        "unique_shared_warmup_targets": 30000000,
        "post_targets_per_study": 48000000,
        "post_targets_total": 144000000,
        "selection_reserve_per_study": 7200000,
        "grand_total_including_full_reserve": 195600000,
        "gpu_hours_cap_per_study": None,
        "colab_cost": None,
        "C_bank": "pending genuine initializations; grammar-constrained collection/matching then bind immutable plan",
        "warmup_corpus_sha256": sha256(args.warmup),
    }
    write_json(root / "registry.json", registry, replace=True)
    print(
        f"Ready registry: {root / 'registry.json'}; 6 shared warm-ups + 72 post jobs planned, zero executed."
    )


if __name__ == "__main__":
    main()
