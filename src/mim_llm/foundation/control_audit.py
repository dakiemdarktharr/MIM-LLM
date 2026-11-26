"""Audit the old byte-matched numeric nuisance control under a frozen BPE."""

from collections import Counter

from ..q3a.data import validate_bundle
from ..q3a.io import read_rows, sha256, source_sha256


def edit_distance(a, b):
    """Exact token Levenshtein distance, trimming shared prefixes/suffixes."""
    left = 0
    while left < min(len(a), len(b)) and a[left] == b[left]:
        left += 1
    a, b = a[left:], b[left:]
    right = 0
    while right < min(len(a), len(b)) and a[-right - 1] == b[-right - 1]:
        right += 1
    if right:
        a, b = a[:-right], b[:-right]
    previous = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        current = [i]
        for j, y in enumerate(b, 1):
            current.append(
                min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (x != y))
            )
        previous = current
    return previous[-1]


def control_stats(bundle, tokenizer):
    validate_bundle(bundle)
    s = bundle["scenarios"]
    tokens = {
        r: tokenizer.encode(s[r]["prompt"], bos=True)
        for r in ("base", "noop", "surface")
    }
    lengths = {r: len(x) for r, x in tokens.items()}
    distances = {
        r: edit_distance(tokens["base"], tokens[r]) for r in ("noop", "surface")
    }
    hamming = {
        r: (
            sum(a != b for a, b in zip(tokens["base"], tokens[r]))
            if lengths["base"] == lengths[r]
            else None
        )
        for r in ("noop", "surface")
    }
    target_ids = {
        r: tokenizer.encode(s[r]["reference"], eos=True)
        for r in ("base", "noop", "surface")
    }
    # Also exercises the generation/training BPE boundary, without fitting.
    for role in ("base", "noop", "surface"):
        tokenizer.response_example(s[role]["prompt"], s[role]["reference"])
    return {
        "source_id": bundle["source_id"],
        "prompt_lengths": lengths,
        "edit_distances": distances,
        "hamming": hamming,
        "same_A1_A2_input_length": lengths["noop"] == lengths["surface"],
        "same_A1_A2_edit_distance": distances["noop"] == distances["surface"],
        "same_A1_A2_hamming": hamming["noop"] == hamming["surface"],
        "same_invariant_targets": target_ids["base"]
        == target_ids["noop"]
        == target_ids["surface"],
    }


def audit_control(path, tokenizer):
    rows = read_rows(path)
    if any(r["split"] != "train" for r in rows):
        raise ValueError("This prospective audit inspects only training bundles")
    if len({r["source_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate source cluster")
    counts = Counter()
    mismatches = []
    for bundle in rows:
        result = control_stats(bundle, tokenizer)
        keys = (
            "same_A1_A2_input_length",
            "same_A1_A2_edit_distance",
            "same_A1_A2_hamming",
            "same_invariant_targets",
        )
        for key in keys:
            counts[key] += result[key]
        if not all(result[k] for k in keys):
            mismatches.append(result)
    return {
        "train_sources": len(rows),
        "counts": dict(counts),
        "mismatches": mismatches,
        "input_sha256": sha256(path),
        "tokenizer_spec": tokenizer.spec,
        "audit_source_sha256": source_sha256(__file__),
        "model_or_tokenizer_updates": 0,
        "validation_test_inspected": False,
        "matched_token_counts_do_not_prove_lexical_or_causal_equivalence": True,
    }
