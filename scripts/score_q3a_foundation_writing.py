"""Summarize the frozen feasibility rule after real author-reader CSV ratings."""

import argparse
import json

from mim_llm.q3a.io import write_json
from mim_llm.q3a_subword.writing_decision import decide


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "review-directory",
        "manifest",
        "packet-directory",
        "labels",
        "rule",
        "output",
    ):
        parser.add_argument("--" + name, required=True)
    a = parser.parse_args()
    result = decide(
        a.review_directory, a.manifest, a.packet_directory, a.labels, a.rule
    )
    write_json(a.output, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
