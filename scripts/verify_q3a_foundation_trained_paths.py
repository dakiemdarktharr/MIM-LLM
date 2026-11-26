"""Check a copied learned foundation checkpoint without any optimizer update."""

import argparse
import json

import torch

from mim_llm.q3a_subword.trained_paths import verify_checkpoint


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", required=True)
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--device", default="cpu")
    args = p.parse_args()
    torch.set_num_threads(2)
    report = verify_checkpoint(
        args.plan, args.checkpoint, args.run_id, args.output, device=args.device
    )
    print(json.dumps({k: v for k, v in report.items() if k != "checks"}), flush=True)
    if not report["passed_in_tested_scope"]:
        raise RuntimeError("Trained path mismatch; retain evidence and stop expansion")


if __name__ == "__main__":
    main()
