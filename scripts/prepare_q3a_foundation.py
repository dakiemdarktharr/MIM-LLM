"""Prepare source-preserving subword foundation inputs, without model updates."""

import argparse
import json
from pathlib import Path

from mim_llm.foundation.codec import GPT_NEO_SPEC, FrozenTokenizer
from mim_llm.foundation.corpus import encode_corpus, expand_normalized
from mim_llm.q3a.io import read_json, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", required=True)
    parser.add_argument("--expanded", required=True)
    parser.add_argument("--encoded", required=True)
    parser.add_argument("--tokenizer", required=True)
    parser.add_argument("--train-stories", type=int, default=300_000)
    parser.add_argument("--context", type=int, default=1024)
    args = parser.parse_args()
    expanded = Path(args.expanded)
    if expanded.exists():
        m = read_json(str(expanded) + ".manifest.json")
        if (
            m["sha256"] != sha256(expanded)
            or m["counts"]["train"] != args.train_stories
            or m["expansion"]["previous_corpus_sha256"] != sha256(args.original)
            or not m.get("normalized_exclusion")
        ):
            raise ValueError("Existing expansion is not the expected foundation input")
        print("Verified existing source expansion; not overwritten.", flush=True)
    else:
        print(
            "Expanding pinned upstream training stories; preserving old rows/splits.",
            flush=True,
        )
        m = expand_normalized(args.original, expanded, train_stories=args.train_stories)
    print(
        json.dumps(
            {
                "expanded_counts": m["counts"],
                "sha256": m["sha256"],
                "normalized_exclusion": m["normalized_exclusion"],
            }
        ),
        flush=True,
    )
    tokenizer = FrozenTokenizer(args.tokenizer, GPT_NEO_SPEC)
    print(
        "Encoding train/validation, retaining long LM stories via reset windows.",
        flush=True,
    )
    encoded = encode_corpus(expanded, args.encoded, tokenizer, context=args.context)
    print(
        json.dumps(
            {
                "encoded": args.encoded,
                "splits": encoded["splits"],
                "test_tokenized": False,
                "optimizer_updates": 0,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
