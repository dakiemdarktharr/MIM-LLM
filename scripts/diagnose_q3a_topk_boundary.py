"""Nonupdating top-k boundary diagnosis; never overrides a failed receipt."""

import argparse
import json
from pathlib import Path

import torch

from mim_llm.foundation.modeling import FoundationConfig, build_foundation
from mim_llm.foundation.plan import load_plan
from mim_llm.q3a.io import sha256, source_sha256, write_json
from mim_llm.q3a_subword.trained_paths import selected_inputs, weights_sha256


def policy(scores, *, temperature=0.8, top_k=40):
    values, indices = (scores / temperature).topk(min(top_k, scores.shape[-1]), -1)
    return torch.zeros_like(scores).scatter(-1, indices, values.softmax(-1))


def boundary_rows(actual, reference, mask, *, top_k=40, limit=5):
    """Retain discrete membership changes, including their original positions.

    Actual policy runs on its native device; the old diagnostic moved logits
    to CPU first. Both are retained, not silently treated as equivalent.
    """
    positions = mask.nonzero().cpu()
    left, right = actual[mask], reference[mask.cpu()]
    rows, maximum, cpu_maximum, cast_reference_maximum = [], 0.0, 0.0, 0.0
    for start in range(0, len(left), 8):
        a, r = left[start : start + 8], right[start : start + 8]
        p = policy(a.float(), top_k=top_k).double().cpu()
        cpu_p = policy(a.float().cpu(), top_k=top_k).double()
        q = policy(r.double(), top_k=top_k)
        cast_q = policy(r.float(), top_k=top_k).double()
        errors = (p - q).abs().sum(-1)
        maximum = max(maximum, float(errors.max()))
        cpu_maximum = max(cpu_maximum, float((cpu_p - q).abs().sum(-1).max()))
        cast_reference_maximum = max(
            cast_reference_maximum, float((p - cast_q).abs().sum(-1).max())
        )
        for offset, error in enumerate(errors):
            if error <= 1e-4:
                continue
            av, ai = a[offset].float().cpu().topk(top_k + 1)
            rv, ri = r[offset].double().topk(top_k + 1)
            a_set, r_set = set(ai[:top_k].tolist()), set(ri[:top_k].tolist())
            rows.append(
                {
                    "position_batch_time": positions[start + offset].tolist(),
                    "native_policy_L1": float(error),
                    "old_CPU_policy_L1": float((cpu_p[offset] - q[offset]).abs().sum()),
                    "max_logit_error": float(
                        (a[offset].double().cpu() - r[offset]).abs().max()
                    ),
                    "actual_raw_cutoff_margin_40_41": float(av[-2] - av[-1]),
                    "reference_raw_cutoff_margin_40_41": float(rv[-2] - rv[-1]),
                    "actual_cutoff_ids": ai[-2:].tolist(),
                    "reference_cutoff_ids": ri[-2:].tolist(),
                    "only_in_actual_CPU_topk": sorted(a_set - r_set),
                    "only_in_reference_topk": sorted(r_set - a_set),
                    "native_actual_support": (p[offset] > 0)
                    .nonzero()
                    .flatten()
                    .tolist(),
                    "reference_support": (q[offset] > 0).nonzero().flatten().tolist(),
                }
            )
    rows.sort(key=lambda row: -row["native_policy_L1"])
    return {
        "positions": len(left),
        "positions_over_unchanged_L1_limit": len(rows),
        "max_native_policy_L1": maximum,
        "max_old_CPU_policy_L1": cpu_maximum,
        "max_native_vs_FP64_logits_cast_to_FP32_policy_L1": cast_reference_maximum,
        "largest_boundary_events": rows[:limit],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("plan", "checkpoint", "run-id", "output"):
        parser.add_argument("--" + key, required=True)
    parser.add_argument("--device", default="cuda")
    a = parser.parse_args()
    if Path(a.output).exists():
        raise FileExistsError(a.output)
    torch.set_num_threads(2)
    torch.backends.mha.set_fastpath_enabled(False)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    plan = load_plan(a.plan)
    digest = sha256(a.checkpoint)
    saved = torch.load(a.checkpoint, map_location="cpu", weights_only=True)
    run = next(r for r in plan["runs"] if r["id"] == a.run_id)
    if (
        saved["identity"]["plan_id"] != plan["plan_id"]
        or saved["identity"]["run"] != run
    ):
        raise ValueError("Wrong learned checkpoint")
    cfg = FoundationConfig(**plan["models"][run["kind"]]["config"])
    actual, reference = (
        build_foundation(cfg).to(a.device),
        build_foundation(cfg).double(),
    )
    actual.load_state_dict(saved["model"])
    reference.load_state_dict(saved["model"])
    del saved
    actual.eval()
    reference.eval()
    before = weights_sha256(actual), weights_sha256(reference)
    cases = []
    with torch.inference_mode():
        for split, indices, batch in selected_inputs(plan, a.device):
            if batch["input_ids"].shape[1] < 641:
                continue
            ids, mask = batch["input_ids"], batch["attention_mask"]
            expected = reference(ids.cpu(), mask.cpu())[0]
            dense = actual(ids, mask)[0]
            value = boundary_rows(dense, expected, mask)
            del dense
            cases.append(
                {"split": split, "indices": indices, "time": ids.shape[1], **value}
            )
    result = {
        "purpose": "boundary diagnosis only, not a passed gate or training permission",
        "plan_id": plan["plan_id"],
        "run": run,
        "checkpoint_sha256": digest,
        "implementation_sha256": source_sha256(__file__),
        "torch": str(torch.__version__),
        "device": a.device,
        "gpu": torch.cuda.get_device_name() if a.device.startswith("cuda") else None,
        "optimizer_updates": 0,
        "test_access": False,
        "weights_and_checkpoint_unchanged": before
        == (weights_sha256(actual), weights_sha256(reference))
        and digest == sha256(a.checkpoint),
        "cases": cases,
    }
    write_json(a.output, result)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
