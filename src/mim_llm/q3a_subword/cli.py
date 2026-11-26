"""Subword evaluation preparation; no training command or automatic test release."""

import argparse
import json

from ..q3a.io import write_json
from .analysis import reviewed_analyze
from .evaluate import freeze_selection, generate_panel, prepare_blind_packet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    freeze = sub.add_parser("freeze-selection")
    freeze.add_argument("--plan", required=True)
    freeze.add_argument("--checkpoints", nargs="+", required=True)
    freeze.add_argument("--registration", required=True)
    freeze.add_argument("--validation-evidence", nargs="+", required=True)
    freeze.add_argument("--rationale", required=True)
    freeze.add_argument("--output", required=True)
    generation = sub.add_parser("generate")
    generation.add_argument("--plan", required=True)
    generation.add_argument("--checkpoint", required=True)
    generation.add_argument(
        "--split", choices=["validation", "test"], default="validation"
    )
    generation.add_argument("--device", default="cpu")
    generation.add_argument("--selection")
    generation.add_argument("--output", required=True)
    packet = sub.add_parser("blind-packet")
    packet.add_argument("--plan", required=True)
    packet.add_argument("--generations", nargs="+", required=True)
    packet.add_argument("--selection")
    packet.add_argument("--output", required=True)
    analysis = sub.add_parser("analyze")
    for name in ["plan", "labels-a", "labels-b", "key", "output"]:
        analysis.add_argument("--" + name, required=True)
    analysis.add_argument("--generations", nargs="+", required=True)
    analysis.add_argument("--selection")
    analysis.add_argument("--adjudicated")
    analysis.add_argument("--draws", type=int, default=2000)
    a = parser.parse_args()
    if a.command == "freeze-selection":
        result = freeze_selection(
            a.plan,
            a.checkpoints,
            a.registration,
            a.output,
            rationale=a.rationale,
            validation_evidence=a.validation_evidence,
        )
        result = {
            k: v
            for k, v in result.items()
            if k not in {"checkpoints", "analysis_registration"}
        }
    elif a.command == "generate":
        result = generate_panel(
            a.plan,
            a.checkpoint,
            a.output,
            split=a.split,
            device=a.device,
            selection=a.selection,
        )
    elif a.command == "blind-packet":
        result = prepare_blind_packet(
            a.plan, a.generations, a.output, selection=a.selection
        )
    else:
        result = reviewed_analyze(
            a.plan,
            a.labels_a,
            a.labels_b,
            a.key,
            a.generations,
            selection=a.selection,
            adjudicated=a.adjudicated,
            draws=a.draws,
        )
        write_json(a.output, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
