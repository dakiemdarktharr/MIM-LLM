"""Train-only compatibility audit; no model creation, optimizer or test read."""

import argparse
import json
from collections import Counter

from mim_llm.foundation.codec import GPT_NEO_SPEC, FrozenTokenizer
from mim_llm.q3a.io import read_rows, sha256, source_sha256, write_json
from mim_llm.q3a_subword.objectives import QUESTIONS, encode_example, probe_rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", required=True)
    parser.add_argument("--tokenizer", required=True)
    parser.add_argument("--context", type=int, default=1024)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    tokenizer = FrozenTokenizer(args.tokenizer, GPT_NEO_SPEC)
    counts = Counter()
    maximum = 0
    for bundle in read_rows(args.train):
        if bundle["split"] != "train":
            raise ValueError("Only training bundles may be audited here")
        counts["source_bundles"] += 1
        for scenario in bundle["scenarios"].values():
            row = encode_example(
                tokenizer, scenario["prompt"], scenario["reference"], args.context
            )
            maximum = max(maximum, len(row["input_ids"]))
            counts["story_CE_rows"] += 1
        for key in QUESTIONS:
            rows = probe_rows(tokenizer, bundle, args.context, key)
            a, b = [[t for t in r["targets"] if t != -100] for r in rows]
            if a != b or a[-1] != tokenizer.eos_id:
                raise ValueError("Probe answer alignment/EOS mismatch")
            counts["invariant_probe_pairs"] += 1
            counts["probe_rows"] += 2
            maximum = max(maximum, *(len(r["input_ids"]) for r in rows))
    if not counts["source_bundles"]:
        raise ValueError("Empty training input")
    result = {
        "input_sha256": sha256(args.train),
        "tokenizer_spec": GPT_NEO_SPEC,
        "counts": dict(counts),
        "maximum_input_tokens": maximum,
        "context": args.context,
        "stable_prompt_response_boundaries": True,
        "model_created": False,
        "optimizer_updates": 0,
        "tokenizer_updates": 0,
        "validation_test_read": False,
        "source_sha256": source_sha256(__file__),
        "objective_source_sha256": source_sha256(
            "src/mim_llm/q3a_subword/objectives.py"
        ),
        "not_a_released_post_training_plan": True,
    }
    write_json(args.output, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
