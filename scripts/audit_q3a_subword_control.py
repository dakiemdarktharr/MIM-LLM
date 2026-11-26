"""Training-source-only prospective BPE control audit, with no optimization."""

import argparse
import json

from mim_llm.foundation.codec import GPT_NEO_SPEC, FrozenTokenizer
from mim_llm.foundation.control_audit import audit_control
from mim_llm.q3a.io import write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tokenizer", required=True)
    parser.add_argument("--train", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    tokenizer = FrozenTokenizer(args.tokenizer, GPT_NEO_SPEC)
    report = audit_control(args.train, tokenizer)
    write_json(args.output, report)
    print(json.dumps({k: v for k, v in report.items() if k != "mismatches"}, indent=2))
    print("Mismatch sources:", len(report["mismatches"]))


if __name__ == "__main__":
    main()
