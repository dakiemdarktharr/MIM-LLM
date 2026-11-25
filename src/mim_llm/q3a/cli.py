"""Q3-A preparation CLI. No command implicitly starts training."""

from __future__ import annotations

import argparse
import json

from .data import prepare, verify_dataset
from .plan import freeze_selection, make_plan


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    q = sub.add_parser("prepare")
    q.add_argument("--output", required=True)
    for split, n in [("train", 6000), ("validation", 400), ("test", 400)]:
        q.add_argument(f"--{split}-sources", type=int, default=n)
    q.add_argument("--seed", type=int, default=2026)
    q = sub.add_parser("verify-data")
    q.add_argument("--data", required=True)
    q = sub.add_parser("fetch-warmup")
    q.add_argument("--output", required=True)
    q.add_argument("--train-stories", type=int, default=3000)
    q.add_argument("--validation-stories", type=int, default=300)
    q.add_argument("--test-stories", type=int, default=300)
    q.add_argument("--revision", default="f54c09fd23315a6f9c86f9dc80f725de7d8f9c64")
    q = sub.add_parser("plan")
    q.add_argument("--config", default="configs/q3a/pilot.json")
    q.add_argument("--data", required=True)
    q.add_argument("--warmup", required=True)
    q.add_argument("--output", required=True)
    q = sub.add_parser("preflight")
    q.add_argument("--plan", required=True)
    q.add_argument("--output", required=True)
    q.add_argument("--device", default="cpu")
    q = sub.add_parser("budget")
    q.add_argument("--plan", required=True)
    q.add_argument("--measurement")
    q = sub.add_parser("train")
    q.add_argument("--plan", required=True)
    q.add_argument("--run-id", required=True)
    q.add_argument("--output-root", required=True)
    q.add_argument("--seconds-limit", type=float, required=True)
    q.add_argument("--device", default="cpu")
    q.add_argument("--resume", action="store_true")
    q = sub.add_parser("freeze-selection")
    q.add_argument("--plan", required=True)
    q.add_argument("--checkpoints", nargs="+", required=True)
    q.add_argument("--output", required=True)
    q.add_argument("--rationale", required=True)
    q.add_argument("--registration", required=True)
    q = sub.add_parser("generate")
    q.add_argument("--plan", required=True)
    q.add_argument("--checkpoint", required=True)
    q.add_argument("--output", required=True)
    q.add_argument("--split", choices=["validation", "test"], default="validation")
    q.add_argument("--device", default="cpu")
    q.add_argument("--selection")
    q = sub.add_parser("perplexity")
    q.add_argument("--plan", required=True)
    q.add_argument("--checkpoint", required=True)
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
    q = sub.add_parser("transfer-template")
    q.add_argument("--output", required=True)
    a = p.parse_args()
    kw = vars(a).copy()
    command = kw.pop("command")
    if command == "prepare":
        result = prepare(**kw)
    elif command == "verify-data":
        result = verify_dataset(a.data)
    elif command == "fetch-warmup":
        from ..ingest import fetch_tinystories

        result = fetch_tinystories(
            a.output,
            train_stories=a.train_stories,
            validation_stories=a.validation_stories,
            test_stories=a.test_stories,
            revision=a.revision,
        )
    elif command == "plan":
        result = make_plan(a.config, a.data, a.warmup, a.output)
    elif command == "preflight":
        from .preflight import preflight

        result = preflight(a.plan, a.output, device=a.device)
    elif command == "budget":
        from .preflight import compute_budget

        result = compute_budget(a.plan, a.measurement)
    elif command == "train":
        from .runner import execute

        result = execute(
            a.plan,
            a.run_id,
            a.output_root,
            seconds_limit=a.seconds_limit,
            device=a.device,
            resume=a.resume,
        )
    elif command == "freeze-selection":
        result = freeze_selection(
            a.plan,
            a.checkpoints,
            a.output,
            rationale=a.rationale,
            registration=a.registration,
        )
    elif command == "generate":
        from .evaluate import generate_panel

        result = generate_panel(
            a.plan,
            a.checkpoint,
            a.output,
            split=a.split,
            device=a.device,
            selection=a.selection,
        )
    elif command == "perplexity":
        from .evaluate import perplexity

        result = perplexity(a.plan, a.checkpoint, device=a.device)
    elif command == "blind-packet":
        from .evaluate import blind_packet

        result = blind_packet(a.generations, a.output)
    elif command == "results-table":
        from .report import results_table

        results_table(a.analysis, a.output)
        result = {"table": a.output}
    elif command == "transfer-template":
        from .report import transfer_template

        transfer_template(a.output)
        result = {"template": a.output, "human_data_created": False}
    else:
        from .evaluate import analyze

        result = analyze(
            a.labels_a, a.labels_b, a.key, adjudicated=a.adjudicated, draws=a.draws
        )
    if command == "analyze":
        from .io import write_json

        write_json(a.output, result)
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
