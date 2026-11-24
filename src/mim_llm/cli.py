"""Command line entry points for local experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from torch.utils.data import DataLoader

from .annotation import (
    finalize_adjudication,
    make_adjudication_packet,
    reader_agreement,
)
from .benchmark import write_benchmark, write_demo_corpus
from .data import StoryDataset, collate, load_jsonl
from .evaluation import (
    aggregate_labels,
    lock_benchmark,
    make_blind_packet,
    run_generations,
)
from .generate import generate
from .ingest import fetch_tinystories
from .matrix import run_matrix
from .models import ModelConfig, build_model, parameter_count
from .protocol import PAPER_TRACKS, match_width
from .tokenizer_train import train_tokenizer
from .train import (
    evaluate_loss,
    file_sha256,
    load_checkpoint,
    load_checkpoint_tokenizer,
    train,
)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="mimlm")
    commands = root.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("make-demo", help="Create self-generated smoke corpus")
    demo.add_argument("output")
    demo.add_argument("--stories", type=int, default=500)
    tiny = commands.add_parser(
        "fetch-tinystories",
        help="Stream a bounded, pinned subset of the public dataset",
    )
    tiny.add_argument("output")
    tiny.add_argument("--train-stories", type=int, default=3000)
    tiny.add_argument("--validation-stories", type=int, default=300)
    tiny.add_argument("--test-stories", type=int, default=300)
    tiny.add_argument("--seed", type=int, default=2026)
    tiny.add_argument("--revision")
    fit_tokenizer = commands.add_parser("train-tokenizer")
    fit_tokenizer.add_argument("--corpus", required=True)
    fit_tokenizer.add_argument("--output", required=True)
    fit_tokenizer.add_argument("--vocab-size", type=int, default=2048)
    bench = commands.add_parser("make-benchmark", help="Create paired synthetic pilot")
    bench.add_argument("output")
    bench.add_argument("--pairs", type=int, default=100)
    lock = commands.add_parser("lock-benchmark")
    lock.add_argument("--benchmark", required=True)
    lock.add_argument("--output", required=True)
    sizes = commands.add_parser("model-size")
    match = commands.add_parser("match-width")
    fit = commands.add_parser("train")
    for command in (sizes, match, fit):
        command.add_argument("--kind", default="mim")
        command.add_argument("--width", type=int, default=192)
        command.add_argument("--layers", type=int, default=2)
        command.add_argument("--context", type=int, default=256)
        command.add_argument("--dropout", type=float, default=0.0)
        command.add_argument("--state-classes", type=int, default=0)
        command.add_argument("--vocab-size", type=int, default=259)
        command.add_argument(
            "--difference-mode", choices=("direct", "cascade"), default="direct"
        )
    match.add_argument("--target-parameters", type=int, required=True)
    fit.add_argument("--corpus", required=True)
    fit.add_argument("--output", required=True)
    fit.add_argument("--seed", type=int, default=0)
    fit.add_argument("--batch-size", type=int, default=8)
    fit.add_argument("--max-train-tokens", type=int, default=100_000)
    fit.add_argument("--lr", type=float, default=3e-4)
    fit.add_argument("--state-loss-weight", type=float, default=0.0)
    fit.add_argument("--device", default="auto")
    fit.add_argument("--tokenizer-model")
    fit.add_argument("--resume", action="store_true")
    fit.add_argument("--checkpoint-every-updates", type=int, default=100)
    matrix = commands.add_parser(
        "matrix", help="Plan matched runs; --run executes them"
    )
    matrix.add_argument("--corpus", required=True)
    matrix.add_argument("--output", required=True)
    matrix.add_argument("--tokenizer-model")
    matrix.add_argument("--reference-width", type=int, default=192)
    matrix.add_argument("--layers", type=int, default=2)
    matrix.add_argument("--context", type=int, default=256)
    matrix.add_argument("--kinds", default="mim,mim_pair")
    matrix.add_argument("--seeds", default="0,1,2")
    matrix.add_argument("--max-train-tokens", type=int, default=100_000)
    matrix.add_argument("--batch-size", type=int, default=8)
    matrix.add_argument("--lr", type=float, default=3e-4)
    matrix.add_argument("--device", default="auto")
    matrix.add_argument("--run", action="store_true")
    sample = commands.add_parser("generate")
    sample.add_argument("--checkpoint", required=True)
    sample.add_argument("--prompt", required=True)
    sample.add_argument("--max-new-tokens", type=int, default=160)
    sample.add_argument("--seed", type=int, default=0)
    sample.add_argument("--temperature", type=float, default=0.8)
    sample.add_argument("--top-k", type=int, default=40)
    sample.add_argument("--device", default="auto")
    ppl = commands.add_parser("perplexity")
    ppl.add_argument("--checkpoint", required=True)
    ppl.add_argument("--corpus", required=True)
    ppl.add_argument("--split", choices=("validation", "test"), default="test")
    ppl.add_argument("--batch-size", type=int, default=8)
    ppl.add_argument("--device", default="auto")
    runs = commands.add_parser("evaluate")
    runs.add_argument("--checkpoint", required=True)
    runs.add_argument("--benchmark", required=True)
    runs.add_argument("--output", required=True)
    runs.add_argument("--seed", type=int, default=0)
    runs.add_argument("--max-new-tokens", type=int, default=200)
    runs.add_argument("--temperature", type=float, default=0.8)
    runs.add_argument("--top-k", type=int, default=40)
    runs.add_argument("--self-events", action="store_true")
    runs.add_argument("--device", default="auto")
    runs.add_argument(
        "--split", choices=("train", "validation", "test", "all"), default="test"
    )
    runs.add_argument("--lock-file")
    blind = commands.add_parser("blind-packet")
    blind.add_argument("--generations", nargs="+", required=True)
    blind.add_argument("--output", required=True)
    blind.add_argument("--key-output", required=True)
    blind.add_argument("--seed", type=int, default=0)
    score = commands.add_parser("aggregate-labels")
    score.add_argument("--labels", required=True)
    score.add_argument("--key", required=True)
    score.add_argument("--draws", type=int, default=2000)
    agree = commands.add_parser("agreement")
    agree.add_argument("--rater-a", required=True)
    agree.add_argument("--rater-b", required=True)
    adjudicate = commands.add_parser("adjudication-packet")
    adjudicate.add_argument("--rater-a", required=True)
    adjudicate.add_argument("--rater-b", required=True)
    adjudicate.add_argument("--output", required=True)
    finalize = commands.add_parser("finalize-adjudication")
    finalize.add_argument("--packet", required=True)
    finalize.add_argument("--output", required=True)
    commands.add_parser("paper-tracks")
    return root


def main() -> None:
    args = parser().parse_args()
    if args.command == "make-demo":
        write_demo_corpus(args.output, stories=args.stories)
    elif args.command == "fetch-tinystories":
        print(
            json.dumps(
                fetch_tinystories(
                    args.output,
                    train_stories=args.train_stories,
                    validation_stories=args.validation_stories,
                    test_stories=args.test_stories,
                    seed=args.seed,
                    revision=args.revision,
                ),
                indent=2,
            )
        )
    elif args.command == "train-tokenizer":
        print(
            json.dumps(
                train_tokenizer(args.corpus, args.output, vocab_size=args.vocab_size),
                indent=2,
            )
        )
    elif args.command == "matrix":
        print(
            json.dumps(
                run_matrix(
                    args.corpus,
                    args.output,
                    tokenizer_model=args.tokenizer_model,
                    reference_width=args.reference_width,
                    layers=args.layers,
                    context=args.context,
                    kinds=args.kinds.split(","),
                    seeds=[int(value) for value in args.seeds.split(",")],
                    max_train_tokens=args.max_train_tokens,
                    batch_size=args.batch_size,
                    learning_rate=args.lr,
                    device=args.device,
                    run=args.run,
                ),
                indent=2,
            )
        )
    elif args.command == "make-benchmark":
        write_benchmark(args.output, pairs=args.pairs)
    elif args.command == "lock-benchmark":
        print(json.dumps(lock_benchmark(args.benchmark, args.output), indent=2))
    elif args.command in {"model-size", "match-width", "train"}:
        config = ModelConfig(
            kind=args.kind,
            width=args.width,
            layers=args.layers,
            context=args.context,
            dropout=args.dropout,
            state_classes=args.state_classes,
            difference_mode=args.difference_mode,
            vocab_size=args.vocab_size,
        )
        if args.command == "model-size":
            print(
                json.dumps(
                    {
                        "config": vars(args),
                        "trainable_parameters": parameter_count(build_model(config)),
                    },
                    indent=2,
                )
            )
        elif args.command == "match-width":
            print(json.dumps(match_width(args.target_parameters, config), indent=2))
        else:
            print(
                json.dumps(
                    train(
                        args.corpus,
                        args.output,
                        config,
                        seed=args.seed,
                        batch_size=args.batch_size,
                        learning_rate=args.lr,
                        max_train_tokens=args.max_train_tokens,
                        state_loss_weight=args.state_loss_weight,
                        device=args.device,
                        tokenizer_model=args.tokenizer_model,
                        resume=args.resume,
                        checkpoint_every_updates=args.checkpoint_every_updates,
                    ),
                    indent=2,
                )
            )
    elif args.command == "generate":
        model, saved = load_checkpoint(args.checkpoint, device=args.device)
        tokenizer = load_checkpoint_tokenizer(args.checkpoint, saved)
        print(
            json.dumps(
                generate(
                    model,
                    tokenizer,
                    args.prompt,
                    max_new_tokens=args.max_new_tokens,
                    seed=args.seed,
                    temperature=args.temperature,
                    top_k=args.top_k,
                    device=next(model.parameters()).device,
                ),
                ensure_ascii=True,
                indent=2,
            )
        )
    elif args.command == "perplexity":
        model, saved = load_checkpoint(args.checkpoint, device=args.device)
        manifest = json.loads(
            (Path(args.checkpoint).parent / "manifest.json").read_text(encoding="utf-8")
        )
        if file_sha256(args.corpus) != manifest["corpus_sha256"]:
            raise ValueError("Corpus checksum differs from training manifest")
        tokenizer = load_checkpoint_tokenizer(args.checkpoint, saved)
        dataset = StoryDataset(
            load_jsonl(args.corpus), tokenizer, args.split, model.config.context
        )
        result = evaluate_loss(
            model,
            DataLoader(dataset, batch_size=args.batch_size, collate_fn=collate),
            next(model.parameters()).device,
        )
        print(
            json.dumps(
                {
                    "split": args.split,
                    "corpus_sha256": manifest["corpus_sha256"],
                    **result,
                },
                indent=2,
            )
        )
    elif args.command == "evaluate":
        run_generations(
            args.checkpoint,
            args.benchmark,
            args.output,
            seed=args.seed,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_k=args.top_k,
            self_events=args.self_events,
            device=args.device,
            split=args.split,
            lock_file=args.lock_file,
        )
    elif args.command == "blind-packet":
        make_blind_packet(
            args.generations, args.output, args.key_output, seed=args.seed
        )
    elif args.command == "aggregate-labels":
        print(
            json.dumps(
                aggregate_labels(args.labels, args.key, bootstrap_draws=args.draws),
                indent=2,
            )
        )
    elif args.command == "agreement":
        print(json.dumps(reader_agreement(args.rater_a, args.rater_b), indent=2))
    elif args.command == "adjudication-packet":
        print(
            json.dumps(
                make_adjudication_packet(args.rater_a, args.rater_b, args.output),
                indent=2,
            )
        )
    elif args.command == "finalize-adjudication":
        finalize_adjudication(args.packet, args.output)
    elif args.command == "paper-tracks":
        print(json.dumps(PAPER_TRACKS, indent=2))


if __name__ == "__main__":
    main()
