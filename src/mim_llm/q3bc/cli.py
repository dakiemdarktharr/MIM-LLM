"""Preparation and staged execution for independent Q3-B/Q3-C studies."""

from __future__ import annotations

import argparse
import json

from .data import prepare, verify
from .plan import bind_bank, freeze_selection, load_plan, make_plan


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    q = sub.add_parser("prepare")
    q.add_argument("--study", choices=["b", "c"], required=True)
    q.add_argument("--output", required=True)
    for s in ("train", "validation", "test"):
        q.add_argument(f"--{s}-sources", type=int)
    q = sub.add_parser("plan")
    q.add_argument("--study", choices=["b", "c"], required=True)
    q.add_argument("--config", required=True)
    q.add_argument("--data", required=True)
    q.add_argument("--shared-plan", required=True)
    q.add_argument("--output", required=True)
    q = sub.add_parser("verify-data")
    q.add_argument("--data", required=True)
    q = sub.add_parser("status")
    q.add_argument("--plan", required=True)
    q = sub.add_parser("preflight")
    q.add_argument("--plan", required=True)
    q.add_argument("--output", required=True)
    q.add_argument("--device", default="cpu")
    q = sub.add_parser("train")
    q.add_argument("--plan", required=True)
    q.add_argument("--run-id", required=True)
    q.add_argument("--output-root", required=True)
    q.add_argument("--warmup-root")
    q.add_argument("--seconds-limit", type=float, required=True)
    q.add_argument("--device", default="cpu")
    q.add_argument("--resume", action="store_true")
    for command in ("collect-bank", "seal-bank"):
        q = sub.add_parser(command)
        q.add_argument("--shared-plan", required=True)
        q.add_argument("--data", required=True)
        q.add_argument("--warmup-root", required=True)
        q.add_argument("--output", required=True)
        q.add_argument("--device", default="cpu")
        if command == "collect-bank":
            q.add_argument("--source-limit", type=int, default=24)
        else:
            q.add_argument("--bank", required=True)
            q.add_argument("--minimum-sources", type=int, default=30)
            q.add_argument("--max-nll-gap", type=float, default=0.25)
            q.add_argument("--max-length-gap", type=int, default=32)
    q = sub.add_parser("bind-bank")
    q.add_argument("--plan", required=True)
    q.add_argument("--bank", required=True)
    q.add_argument("--output", required=True)
    q = sub.add_parser("freeze-selection")
    q.add_argument("--plan", required=True)
    q.add_argument("--checkpoints", nargs="+", required=True)
    q.add_argument("--registration", required=True)
    q.add_argument("--rationale", required=True)
    q.add_argument("--output", required=True)
    q = sub.add_parser("generate")
    q.add_argument("--plan", required=True)
    q.add_argument("--checkpoint", required=True)
    q.add_argument("--output", required=True)
    q.add_argument("--split", choices=["validation", "test"], default="validation")
    q.add_argument("--selection")
    q.add_argument("--device", default="cpu")
    q = sub.add_parser("probe-evaluate")
    q.add_argument("--plan", required=True)
    q.add_argument("--checkpoint", required=True)
    q.add_argument("--output", required=True)
    q.add_argument("--device", default="cpu")
    q = sub.add_parser("blind-packet")
    q.add_argument("--generations", nargs="+", required=True)
    q.add_argument("--output", required=True)
    q = sub.add_parser("analyze")
    q.add_argument("--labels-a", required=True)
    q.add_argument("--labels-b", required=True)
    q.add_argument("--key", required=True)
    q.add_argument("--adjudicated")
    q.add_argument("--draws", type=int, default=2000)
    q.add_argument("--output", required=True)
    q = sub.add_parser("results-table")
    q.add_argument("--analysis", required=True)
    q.add_argument("--output", required=True)
    q = sub.add_parser("perplexity")
    q.add_argument("--plan", required=True)
    q.add_argument("--checkpoint", required=True)
    q.add_argument("--device", default="cpu")
    q.add_argument("--split", choices=["validation", "test"], default="validation")
    q.add_argument("--selection")
    a = p.parse_args()
    if a.command == "prepare":
        result = prepare(
            a.study,
            a.output,
            train_sources=a.train_sources,
            validation_sources=a.validation_sources,
            test_sources=a.test_sources,
        )
    elif a.command == "plan":
        result = make_plan(a.study, a.config, a.data, a.shared_plan, a.output)
    elif a.command == "verify-data":
        result = verify(a.data)
    elif a.command == "status":
        from ..q3a.io import read_json
        from ..training_gate import POLICY

        plan = load_plan(a.plan)
        policy = read_json(POLICY)
        permitted = bool(
            policy["model_training_authorized"]
            and plan["plan_id"] in policy.get("authorized_plan_ids", [])
        )
        result = {
            "plan_id": plan["plan_id"],
            "study": plan["study"],
            "training_authorized": permitted,
            "authorized_run_ids": sorted(
                {r["id"] for r in plan["runs"]}
                & set(policy.get("authorized_run_ids", []))
            ),
            "warmup": "six shared A-plan initializations, not six additional runs per paper",
            "C_bank_ready": bool(plan["sealed_bank"]) if plan["study"] == "c" else None,
            "next": "wait for user training instruction"
            if not permitted
            else "execute only authorized IDs after dependencies are satisfied",
        }
    elif a.command == "preflight":
        from .preflight import preflight

        result = preflight(a.plan, a.output, device=a.device)
    elif a.command == "train":
        from .runner import execute

        result = execute(
            a.plan,
            a.run_id,
            a.output_root,
            seconds_limit=a.seconds_limit,
            device=a.device,
            resume=a.resume,
            warmup_root=a.warmup_root,
        )
    elif a.command == "collect-bank":
        from .bank import collect

        result = collect(
            a.shared_plan,
            a.data,
            a.warmup_root,
            a.output,
            source_limit=a.source_limit,
            device=a.device,
        )
    elif a.command == "seal-bank":
        from .bank import seal

        result = seal(
            a.shared_plan,
            a.data,
            a.warmup_root,
            a.bank,
            a.output,
            minimum_sources=a.minimum_sources,
            max_nll_gap=a.max_nll_gap,
            max_length_gap=a.max_length_gap,
            device=a.device,
        )
    elif a.command == "bind-bank":
        result = bind_bank(a.plan, a.bank, a.output)
    elif a.command == "freeze-selection":
        result = freeze_selection(
            a.plan, a.checkpoints, a.registration, a.output, rationale=a.rationale
        )
    elif a.command == "generate":
        from .evaluate import generate_panel

        result = generate_panel(
            a.plan,
            a.checkpoint,
            a.output,
            split=a.split,
            selection=a.selection,
            device=a.device,
        )
    elif a.command == "perplexity":
        from .evaluate import perplexity

        result = perplexity(
            a.plan, a.checkpoint, split=a.split, selection=a.selection, device=a.device
        )
    elif a.command == "probe-evaluate":
        from .evaluate import probe_evaluate

        result = probe_evaluate(a.plan, a.checkpoint, a.output, device=a.device)
    elif a.command == "blind-packet":
        from .evaluate import blind_packet

        result = blind_packet(a.generations, a.output)
    elif a.command == "results-table":
        from .report import results_table

        results_table(a.analysis, a.output)
        result = {"table": a.output}
    else:
        from .evaluate import analyze

        result = analyze(
            a.labels_a,
            a.labels_b,
            a.key,
            a.output,
            adjudicated=a.adjudicated,
            draws=a.draws,
        )
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
