"""Incremental, seeded sampling shared by every architecture."""

from __future__ import annotations

import torch
from torch import nn

from .tokenizer import ByteTokenizer, Tokenizer


@torch.inference_mode()
def generate_from_ids(
    model: nn.Module,
    tokenizer: Tokenizer,
    prompt_ids: list[int],
    *,
    max_new_tokens: int = 160,
    temperature: float = 0.8,
    top_k: int = 40,
    seed: int = 0,
    device: str | torch.device = "cpu",
) -> dict[str, object]:
    if max_new_tokens < 1 or temperature <= 0 or top_k < 1:
        raise ValueError("Invalid sampling settings")
    model.eval()
    if not prompt_ids or any(
        token < 0 or token >= tokenizer.vocab_size for token in prompt_ids
    ):
        raise ValueError("Nonempty valid prompt token IDs required")
    if (
        hasattr(model, "config")
        and model.config.kind == "transformer"
        and len(prompt_ids) + max_new_tokens > model.config.context
    ):
        raise ValueError("Transformer prompt plus output exceeds configured context")
    generator = torch.Generator(device=device).manual_seed(seed)
    state = None
    input_ids = torch.tensor([prompt_ids], device=device)
    logits, _, state = model(input_ids, return_state=True)
    next_logits = logits[:, -1]
    emitted: list[int] = []
    for _ in range(max_new_tokens):
        scores = next_logits.float() / temperature
        scores[:, tokenizer.pad_id] = -torch.inf
        scores[:, tokenizer.bos_id] = -torch.inf
        values, indices = torch.topk(scores, min(top_k, scores.shape[-1]), dim=-1)
        probabilities = torch.softmax(values, dim=-1)
        chosen = indices.gather(
            -1, torch.multinomial(probabilities, 1, generator=generator)
        ).squeeze(-1)
        token = int(chosen.item())
        if token == tokenizer.eos_id:
            break
        emitted.append(token)
        logits, _, state = model(chosen[:, None], state=state, return_state=True)
        next_logits = logits[:, -1]
    decoded = tokenizer.decode(emitted)
    valid_utf8 = "\ufffd" not in decoded
    if isinstance(tokenizer, ByteTokenizer):
        raw = bytes(token - 3 for token in emitted if token >= 3)
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            valid_utf8 = False
    return {
        "continuation": decoded,
        "token_ids": emitted,
        "valid_utf8": valid_utf8,
        "seed": seed,
    }


def generate(
    model: nn.Module, tokenizer: Tokenizer, prompt: str, **kwargs
) -> dict[str, object]:
    result = generate_from_ids(
        model, tokenizer, tokenizer.encode(prompt, bos=True), **kwargs
    )
    return {"prompt": prompt, **result}
