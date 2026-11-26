"""Explicit padding masks, exact target caps and loss without unused LM logits."""

import torch
from torch.nn import functional as F


def make_batch(examples, *, pad_id, context, device="cpu", remaining=None):
    if remaining is not None and remaining < 1:
        raise ValueError("Positive remaining target budget required")
    chosen = []
    left = remaining
    for row in examples:
        ids, labels = row["input_ids"], list(row["targets"])
        if len(ids) != len(labels) or not ids:
            raise ValueError("Misaligned or empty shifted example")
        positions = [i for i, x in enumerate(labels) if x != -100]
        if not positions:
            raise ValueError("Example has no supervised tokens")
        if left is not None:
            for i in positions[left:]:
                labels[i] = -100
            positions = positions[:left]
            left -= len(positions)
        end = positions[-1] + 1
        if end > context:
            raise ValueError("No silent context truncation")
        chosen.append((ids[:end], labels[:end]))
        if left == 0:
            break
    if not chosen:
        raise ValueError("Empty batch")
    length = max(len(ids) for ids, _ in chosen)
    inputs = torch.full((len(chosen), length), pad_id, device=device, dtype=torch.long)
    targets = torch.full_like(inputs, -100)
    mask = torch.zeros_like(inputs, dtype=torch.bool)
    for i, (ids, labels) in enumerate(chosen):
        inputs[i, : len(ids)] = torch.tensor(ids, device=device)
        targets[i, : len(ids)] = torch.tensor(labels, device=device)
        mask[i, : len(ids)] = True  # BOS/EOS may share the padding token ID.
    return {"input_ids": inputs, "targets": targets, "attention_mask": mask}


def selected_ce(model, batch):
    selected = batch["targets"] != -100
    count = int(selected.sum())
    if count == 0:
        raise ValueError("No supervised targets")
    features = model.training_features(batch["input_ids"], batch["attention_mask"])
    return F.cross_entropy(
        model.head(features[selected]), batch["targets"][selected]
    ), count
