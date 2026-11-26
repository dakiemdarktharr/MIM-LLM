"""Canonical CPU/FP64 inference, separate from immutable FP32 training.

The FP32 top-k boundary failure remains failed. This higher precision backend
must earn its own unchanged numerical bounds before being used in a real run.
"""

from contextlib import contextmanager

import torch

BACKEND = "CPU_FP64_MHA_off_stable_token_ID_topk_v1"


@contextmanager
def canonical_backend():
    previous = torch.backends.mha.get_fastpath_enabled(), torch.get_num_threads()
    try:
        torch.backends.mha.set_fastpath_enabled(False)
        torch.set_num_threads(2)
        yield
    finally:
        torch.backends.mha.set_fastpath_enabled(previous[0])
        torch.set_num_threads(previous[1])


def require_model(model, device):
    if device != "cpu" or any(
        p.device.type != "cpu" or p.dtype != torch.float64 for p in model.parameters()
    ):
        raise ValueError("Canonical generation requires a CPU/FP64 model copy")


def topk_distribution(logits, *, temperature=0.8, top_k=40):
    """Exactly k tokens; exact score ties are resolved by ascending token ID."""
    if (
        logits.device.type != "cpu"
        or logits.dtype != torch.float64
        or not torch.isfinite(logits).all()
        or temperature <= 0
        or top_k < 1
    ):
        raise ValueError(
            "Finite CPU/FP64 logits and positive decoding settings required"
        )
    scores = logits / temperature
    indices = torch.argsort(scores, dim=-1, descending=True, stable=True)[
        ..., : min(top_k, scores.shape[-1])
    ]
    probabilities = scores.gather(-1, indices).softmax(-1)
    return probabilities, indices


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
    require_model(model, device)
    if max_new_tokens < 1 or temperature <= 0 or top_k < 1:
        raise ValueError("Invalid decoding policy")
    ids = tokenizer.encode(prompt, bos=True)
    if len(ids) + max_new_tokens > model.config.context:
        raise ValueError("Prompt plus generation exceeds declared context")
    with canonical_backend():
        model.eval()
        rng = torch.Generator(device="cpu").manual_seed(seed)
        logits, _, state = model(torch.tensor([ids]), return_state=True)
        emitted, ended = [], False
        for _ in range(max_new_tokens):
            # All currently frozen special IDs are EOS. A future tokenizer with
            # different BOS/PAD IDs needs an explicitly reviewed policy.
            if {tokenizer.pad_id, tokenizer.bos_id} != {tokenizer.eos_id}:
                raise ValueError("Canonical policy requires the frozen shared EOS IDs")
            probabilities, indices = topk_distribution(
                logits[:, -1], temperature=temperature, top_k=top_k
            )
            choice = indices.gather(
                -1, torch.multinomial(probabilities, 1, generator=rng)
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
        "inference_backend": BACKEND,
    }
