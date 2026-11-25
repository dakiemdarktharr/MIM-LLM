"""Shifted response-only CE and probe-span JS, with no optimizer operations."""

from __future__ import annotations

import torch
from torch.nn import functional as F

from ..tokenizer import ByteTokenizer
from .data import state

TOKENIZER = ByteTokenizer()


def encode_example(prompt, response, context):
    prefix = TOKENIZER.encode(prompt, bos=True)
    suffix = TOKENIZER.encode(response, eos=True)
    ids = prefix + suffix
    if len(ids) - 1 > context:
        raise ValueError(f"No truncation allowed: {len(ids) - 1} > {context}")
    return {"input_ids": ids[:-1], "targets": [-100] * (len(prefix) - 1) + suffix}


def batch_examples(examples, context, device="cpu", remaining=None):
    encoded = [
        x if "input_ids" in x else encode_example(x["prompt"], x["reference"], context)
        for x in examples
    ]
    length = max(len(x["input_ids"]) for x in encoded)
    inputs = torch.zeros((len(encoded), length), dtype=torch.long, device=device)
    targets = torch.full_like(inputs, -100)
    mask = torch.zeros_like(inputs, dtype=torch.bool)
    left = remaining
    for i, row in enumerate(encoded):
        n = len(row["input_ids"])
        inputs[i, :n] = torch.tensor(row["input_ids"], device=device)
        mask[i, :n] = True
        labels = torch.tensor(row["targets"], device=device)
        if left is not None:
            positions = (labels != -100).nonzero().flatten()
            labels[positions[max(0, left) :]] = -100
            left = max(0, left - len(positions))
        targets[i, :n] = labels
    return {"input_ids": inputs, "targets": targets, "attention_mask": mask}


def ce_loss(model, batch):
    logits, _ = model(batch["input_ids"], batch["attention_mask"])
    count = int((batch["targets"] != -100).sum().item())
    if not count:
        raise ValueError("No target tokens")
    return F.cross_entropy(
        logits.flatten(0, 1), batch["targets"].flatten(), ignore_index=-100
    ), count


def js_divergence(logits_a, logits_b):
    if logits_a.shape != logits_b.shape:
        raise ValueError("Aligned probe logits required")
    logp = F.log_softmax(logits_a.float(), dim=-1)
    logq = F.log_softmax(logits_b.float(), dim=-1)
    logm = torch.logaddexp(logp, logq) - torch.log(
        torch.tensor(2.0, device=logp.device)
    )
    return (
        0.5
        * (
            (logp.exp() * (logp - logm)).sum(-1) + (logq.exp() * (logq - logm)).sum(-1)
        ).mean()
    )


def probe_js(model, bundle, context, device, probe_key="holder"):
    a = bundle["scenarios"]["base"]
    b = bundle["scenarios"]["noop"]
    # This is train-only supervision; no factual probe/table is given at generation.
    questions = {
        "holder": "Who holds the key at the decision?",
        "action": "Must the holder open or wait at the decision?",
        "cabinet": "Is the cabinet open or locked at the decision?",
        "power_available": "Is power available at the decision?",
        "permission": "Has permission been granted?",
    }
    value = state(a["world"])[probe_key]
    answer = ("yes" if value else "no") if isinstance(value, bool) else value
    if state(b["world"])[probe_key] != value:
        raise ValueError("Probe is not invariant")
    suffix = "\nQuestion: " + questions[probe_key] + "\nAnswer: "
    rows = [encode_example(s["prompt"] + suffix, answer, context) for s in (a, b)]
    batch = batch_examples(
        [{"prompt": s["prompt"] + suffix, "reference": answer} for s in (a, b)],
        context,
        device,
    )
    logits, _ = model(batch["input_ids"], batch["attention_mask"])
    selected = [logits[i, (batch["targets"][i] != -100)] for i in range(2)]
    # EOS is included on both sides; answer length is exactly the same.
    loss = js_divergence(*selected)
    return loss, {
        "probe_input_tokens": int(batch["attention_mask"].sum()),
        "probe_positions": sum(sum(t != -100 for t in r["targets"]) for r in rows),
    }
