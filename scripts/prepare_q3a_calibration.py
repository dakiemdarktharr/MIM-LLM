"""Prepare one prospectively bounded language calibration, without training."""

import argparse
import json

from mim_llm.warmup_calibration import (
    expand_preserving_splits,
    prepare_continuation_warmup,
)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original", required=True)
    p.add_argument("--expanded", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--train-stories", type=int, default=30_000)
    a = p.parse_args()
    expanded = expand_preserving_splits(
        a.original, a.expanded, train_stories=a.train_stories
    )
    formatted = prepare_continuation_warmup(a.expanded, a.output)
    print(
        json.dumps(
            {"expanded": expanded, "warmup": formatted}, ensure_ascii=False, indent=2
        )
    )


if __name__ == "__main__":
    main()
