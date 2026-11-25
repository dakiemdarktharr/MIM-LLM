"""Separate event/probe CE for B; actual chosen-event suffix CE for C."""

from __future__ import annotations

from pathlib import Path

from ..q3a.io import read_rows
from ..q3a.objectives import batch_examples, ce_loss
from ..q3a.runner import language_examples
from .data import b_probe, c_suffix, history_options


def examples_for(plan, run, *, split="train", contract_fixture=False):
    rows = read_rows(Path(plan["data_dir"]) / f"{split}.jsonl")
    if plan["study"] == "b":
        return [
            {"source_id": r["source_id"], "row": r, "index": i}
            for i, r in enumerate(rows)
        ]
    if split == "train" and not contract_fixture:
        if not plan["sealed_bank"]:
            raise ValueError(
                "Genuine matched bank required; teacher fixtures cannot replace self/peer histories"
            )
        return read_rows(Path(plan["sealed_bank"]) / (run["id"] + ".jsonl"))
    # This fixture validates tensor contracts only, never becomes C1/C2 training data.
    out = []
    for r in rows:
        h = next(
            x
            for x in history_options(r)
            if x["place"] == r["teacher_place"] and x["style"] == r["teacher_style"]
        )
        out.append(
            {
                "source_id": r["source_id"],
                "prompt": r["prompt"] + h["text"] + r["followup"],
                "reference": c_suffix(r, h["place"]),
                "contract_fixture": True,
            }
        )
    return out


def loss_batch(model, items, plan, run, *, remaining, device="cpu"):
    context = plan["config"]["context"]
    if plan["study"] == "c":
        batch = batch_examples(items, context, device, remaining=remaining)
        loss, n = ce_loss(model, batch)
        return (
            loss,
            n,
            {
                "event_targets": 0,
                "answer_targets": n,
                "processed_input_tokens": int(batch["attention_mask"].sum()),
                "probe_input_tokens": 0,
            },
        )
    probes = [b_probe(x["row"], run["arm"], x["index"]) for x in items]
    full_probe = batch_examples(probes, context, device)
    probe_n = min(remaining, int((full_probe["targets"] != -100).sum()))
    probe = batch_examples(probes, context, device, remaining=probe_n)
    event_items = []
    for x in items:
        event_items.extend(
            language_examples(
                [
                    {
                        "source_id": x["source_id"],
                        "split": "train",
                        "text": x["row"]["event_text"],
                    }
                ],
                "train",
                context,
            )
        )
    event_budget = max(0, remaining - probe_n)
    event = batch_examples(event_items, context, device, remaining=event_budget)
    event_n = int((event["targets"] != -100).sum())
    probe_loss, _ = ce_loss(model, probe)
    if event_n:
        event_loss, _ = ce_loss(model, event)
        loss = event_loss + plan["config"]["answer_loss_weight"] * probe_loss
    else:
        loss = plan["config"]["answer_loss_weight"] * probe_loss
    inputs = int(probe["attention_mask"].sum()) + (
        int(event["attention_mask"].sum()) if event_n else 0
    )
    return (
        loss,
        event_n + probe_n,
        {
            "event_targets": event_n,
            "answer_targets": probe_n,
            "processed_input_tokens": inputs,
            "probe_input_tokens": int(probe["attention_mask"].sum()),
            "probe_prefix_bytes": sum(x["prefix_bytes"] for x in probes),
            "semantic_write_sum": sum(x["semantic_writes"] for x in probes),
        },
    )


def validation_examples(plan):
    if plan["study"] == "c":
        return examples_for(
            plan, plan["runs"][0], split="validation", contract_fixture=True
        )
    rows = read_rows(Path(plan["data_dir"]) / "validation.jsonl")
    return language_examples(
        [
            {
                "source_id": r["source_id"],
                "split": "validation",
                "text": r["event_text"],
            }
            for r in rows
        ],
        "validation",
        plan["config"]["context"],
    )
