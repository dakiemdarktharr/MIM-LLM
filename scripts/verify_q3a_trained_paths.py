"""Read-only dense/cache/step/causality checks on actual trained checkpoints."""

import argparse
import json
from pathlib import Path

import torch

from mim_llm.q3a.evaluate import load_q3a_checkpoint
from mim_llm.q3a.io import sha256, source_sha256, write_json
from mim_llm.q3a.plan import load_plan
from mim_llm.shared_data import general_rows
from mim_llm.tokenizer import ByteTokenizer


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", required=True)
    p.add_argument("--checkpoint-root", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--device", default="cpu")
    a = p.parse_args()
    if Path(a.output).exists():
        raise FileExistsError(a.output)
    torch.set_num_threads(2)
    plan = load_plan(a.plan)
    tokenizer = ByteTokenizer()
    rows = [r for r in general_rows(plan["warmup"]) if r["split"] == "validation"]
    rows = sorted(
        rows, key=lambda r: (-len(r["text"].encode("utf-8")), r["source_id"])
    )[:3]
    checks = []
    with torch.inference_mode():
        for kind in plan["config"]["backbones"]:
            path = Path(a.checkpoint_root) / f"warmup-{kind}-s0" / "final.pt"
            model, checkpoint = load_q3a_checkpoint(path, plan, a.device)
            declared = next(r for r in plan["runs"] if r["id"] == f"warmup-{kind}-s0")
            if (
                not checkpoint["complete"]
                or model.config.dropout != 0
                or model.config.kind != kind
                or checkpoint["run"] != declared
                or checkpoint["stats"]["trained_targets"] != declared["targets"]
            ):
                raise ValueError("Require complete dropout-zero declared checkpoints")
            for row in rows:
                tokens = tokenizer.encode(row["text"], bos=True)
                for length in (32, 128, 512, 1024):
                    if length > len(tokens) or length > plan["config"]["context"]:
                        continue
                    ids = torch.tensor([tokens[:length]], device=a.device)
                    model.train()
                    dense_train, _ = model(ids)
                    model.eval()
                    dense_eval, _ = model(ids)
                    cached, _, _ = model(ids, return_state=True)
                    state, pieces = None, []
                    for token in ids.split(1, dim=1):
                        logits, _, state = model(token, state=state, return_state=True)
                        pieces.append(logits)
                    step = torch.cat(pieces, dim=1)
                    future = ids.clone()
                    future[:, -1] = (future[:, -1] - 3 + 1) % 256 + 3
                    dense_future, _ = model(future)
                    values = {
                        "dense_train_vs_eval": dense_train - dense_eval,
                        "dense_eval_vs_cached": dense_eval - cached,
                        "cached_full_vs_step": cached - step,
                        "future_edit_vs_past_dense_logits": dense_eval[:, :-1]
                        - dense_future[:, :-1],
                    }
                    matches = {
                        "dense_train_vs_eval": torch.allclose(
                            dense_train, dense_eval, atol=1e-4, rtol=1e-4
                        ),
                        "dense_eval_vs_cached": torch.allclose(
                            dense_eval, cached, atol=1e-4, rtol=1e-4
                        ),
                        "cached_full_vs_step": torch.allclose(
                            cached, step, atol=1e-4, rtol=1e-4
                        ),
                        "future_edit_vs_past_dense_logits": torch.allclose(
                            dense_eval[:, :-1],
                            dense_future[:, :-1],
                            atol=1e-4,
                            rtol=1e-4,
                        ),
                    }
                    checks.append(
                        {
                            "kind": kind,
                            "source_id": row["source_id"],
                            "tokens": length,
                            "checkpoint_sha256": sha256(path),
                            "max_abs_errors": {
                                k: float(v.abs().max()) for k, v in values.items()
                            },
                            "allclose_atol_rtol_1e4": {
                                k: bool(v) for k, v in matches.items()
                            },
                            "all_logits_finite": all(
                                bool(torch.isfinite(v).all())
                                for v in (
                                    dense_train,
                                    dense_eval,
                                    cached,
                                    step,
                                    dense_future,
                                )
                            ),
                        }
                    )
            del model
            if a.device.startswith("cuda"):
                torch.cuda.empty_cache()
    report = {
        "plan_id": plan["plan_id"],
        "source_sha256": source_sha256(__file__),
        "torch": torch.__version__,
        "device": a.device,
        "gpu": torch.cuda.get_device_name() if a.device.startswith("cuda") else None,
        "optimizer_updates": 0,
        "test_access": False,
        "selection": "Three longest original validation stories by UTF-8 bytes, source-ID tiebreak",
        "checks": checks,
        "passed_in_tested_scope": bool(checks)
        and all(
            c["all_logits_finite"] and all(c["allclose_atol_rtol_1e4"].values())
            for c in checks
        ),
    }
    write_json(a.output, report)
    print(json.dumps({k: v for k, v in report.items() if k != "checks"}), flush=True)
    if not report["passed_in_tested_scope"]:
        raise RuntimeError(
            "Trained path mismatch; retain report and investigate before expansion"
        )


if __name__ == "__main__":
    main()
