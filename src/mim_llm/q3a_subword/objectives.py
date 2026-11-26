"""Response CE and train-only component JS with stable subword boundaries.

Generation/evaluation must still require natural story continuations. These
single-answer probes are auxiliary training components, not primary outputs.
"""

from ..foundation.objectives import make_batch, selected_ce
from ..q3a.data import state
from ..q3a.objectives import js_divergence

QUESTIONS = {
    "holder": "Who holds the key at the decision?",
    "action": "Must the holder open or wait at the decision?",
    "cabinet": "Is the cabinet open or locked at the decision?",
    "power_available": "Is power available at the decision?",
    "permission": "Has permission been granted?",
}


def encode_example(tokenizer, prompt, response, context):
    row = tokenizer.response_example(prompt, response)
    if len(row["input_ids"]) > context:
        raise ValueError("No silent context truncation in a subword example")
    return row


def batch_examples(examples, tokenizer, context, device="cpu", remaining=None):
    rows = [
        encode_example(tokenizer, row["prompt"], row["reference"], context)
        for row in examples
    ]
    return make_batch(
        rows,
        pad_id=tokenizer.pad_id,
        context=context,
        device=device,
        remaining=remaining,
    )


def ce_loss(model, batch):
    return selected_ce(model, batch)


def probe_rows(tokenizer, bundle, context, probe_key="holder"):
    factual, noop = [bundle["scenarios"][role] for role in ("base", "noop")]
    value = state(factual["world"])[probe_key]
    if state(noop["world"])[probe_key] != value:
        raise ValueError("Semantic no-op probe changed its target")
    answer = ("yes" if value else "no") if isinstance(value, bool) else value
    # A trailing space may merge with the answer in byte-level BPE. The
    # newline is explicit, checked by FrozenTokenizer, and used at generation.
    suffix = "\nQuestion: " + QUESTIONS[probe_key] + "\nAnswer:\n"
    return [
        encode_example(tokenizer, scenario["prompt"] + suffix, answer, context)
        for scenario in (factual, noop)
    ]


def probe_js(model, tokenizer, bundle, context, device="cpu", probe_key="holder"):
    rows = probe_rows(tokenizer, bundle, context, probe_key)
    batch = make_batch(rows, pad_id=tokenizer.pad_id, context=context, device=device)
    features = model.training_features(batch["input_ids"], batch["attention_mask"])
    selected = [model.head(features[i, batch["targets"][i] != -100]) for i in range(2)]
    loss = js_divergence(*selected)
    return loss, {
        "probe_input_tokens": int(batch["attention_mask"].sum()),
        "probe_positions": sum(
            int((batch["targets"][i] != -100).sum()) for i in range(2)
        ),
        "probe_key": probe_key,
        "EOS_included": True,
        "inference_state_table": False,
    }
