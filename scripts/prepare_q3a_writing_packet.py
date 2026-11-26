"""Create a blank author-reader packet AFTER real foundation generations exist."""

import argparse
import json

from mim_llm.q3a_subword.writing_packet import make_packet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-directory", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            make_packet(args.review_directory, args.manifest, args.output), indent=2
        )
    )


if __name__ == "__main__":
    main()
