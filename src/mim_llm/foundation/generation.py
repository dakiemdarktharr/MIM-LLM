"""Seeded generation with EOS preserved when BOS, EOS and padding share an ID."""

import torch


@torch.inference_mode()
def generate(
    model,
    tokenizer,
    prompt,
    *,
    max_new_tokens=128,
    seed=17,
    temperature=0.8,
    top_k=40,
    device="cpu",
):
    if max_new_tokens < 1 or temperature <= 0 or top_k < 1:
        raise ValueError("Invalid decoding policy")
    ids = tokenizer.encode(prompt, bos=True)
    if len(ids) + max_new_tokens > model.config.context:
        raise ValueError("Prompt plus generation exceeds declared context")
    model.eval()
    rng = torch.Generator(device=device).manual_seed(seed)
    logits, _, state = model(torch.tensor([ids], device=device), return_state=True)
    emitted, ended = [], False
    for _ in range(max_new_tokens):
        scores = logits[:, -1].float() / temperature
        for token in {tokenizer.pad_id, tokenizer.bos_id} - {tokenizer.eos_id}:
            scores[:, token] = -torch.inf
        values, indices = scores.topk(min(top_k, scores.shape[-1]), dim=-1)
        choice = indices.gather(
            -1, torch.multinomial(values.softmax(-1), 1, generator=rng)
        )
        token = int(choice.item())
        if token == tokenizer.eos_id:
            ended = True
            break
        emitted.append(token)
        logits, _, state = model(choice, state=state, return_state=True)
    text = tokenizer.decode(emitted)
    return {
        "prompt": prompt,
        "continuation": text,
        "token_ids": emitted,
        "seed": seed,
        "eos_emitted": ended,
        "cap_reached": not ended and len(emitted) == max_new_tokens,
        "valid_utf8": "\ufffd" not in text,
        "human_label": None,
        "primary_evaluation": False,
    }
