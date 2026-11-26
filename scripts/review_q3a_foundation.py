"""Prepare or generate the fixed foundation writing-feasibility panel."""

import argparse
import json

from mim_llm.q3a_subword.foundation_review import generate_review, prepare_review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--plan", required=True)
    prepare.add_argument("--recipe", required=True)
    prepare.add_argument("--corpus", required=True)
    prepare.add_argument("--output", required=True)
    run = commands.add_parser("generate")
    run.add_argument("--plan", required=True)
    run.add_argument("--manifest", required=True)
    run.add_argument("--checkpoint-root", required=True)
    run.add_argument("--output", required=True)
    run.add_argument("--device", default="cpu")
    args = parser.parse_args()
    if args.command == "prepare":
        value = prepare_review(args.plan, args.recipe, args.corpus, args.output)
        value = {k: v for k, v in value.items() if k != "prompts"}
    else:
        value = generate_review(
            args.plan,
            args.manifest,
            args.checkpoint_root,
            args.output,
            device=args.device,
        )
    print(json.dumps(value, indent=2))


if __name__ == "__main__":
    main()
