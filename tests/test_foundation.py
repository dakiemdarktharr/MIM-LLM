"""Subword boundary/EOS and mathematical inference/loss checks; no optimizer."""

import hashlib
import random
import shutil

import pytest
import torch
from tokenizers import AddedToken, Tokenizer, decoders, models, pre_tokenizers

from mim_llm.foundation.codec import FrozenTokenizer
from mim_llm.foundation.control_audit import edit_distance
from mim_llm.foundation.corpus import (
    TokenDataset,
    encode_corpus,
    expand_normalized,
    language_windows,
)
from mim_llm.foundation.generation import generate
from mim_llm.foundation.modeling import FoundationConfig, build_foundation
from mim_llm.foundation.objectives import make_batch, selected_ce
from mim_llm.q3a.io import read_rows, sha256, write_json, write_rows


@pytest.fixture
def codec(tmp_path):
    # Static byte alphabet + two specified merges, never a fitted tokenizer.
    alphabet = sorted(pre_tokenizers.ByteLevel.alphabet())
    vocab = {letter: index for index, letter in enumerate(alphabet)}
    vocab.update({"hi": 256, "Ġhi": 257, "<|endoftext|>": 258})
    backend = Tokenizer(models.BPE(vocab, [("h", "i"), ("Ġ", "hi")]))
    backend.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    backend.decoder = decoders.ByteLevel()
    backend.add_special_tokens([AddedToken("<|endoftext|>", special=True)])
    path = tmp_path / "static-tokenizer.json"
    backend.save(str(path))
    return FrozenTokenizer(
        path,
        {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "vocab_size": 259,
            "bos_id": 258,
            "eos_id": 258,
            "pad_id": 258,
            "eos_token": "<|endoftext|>",
        },
    )


def model_for(kind, vocab_size=259):
    torch.set_num_threads(2)
    torch.manual_seed(0)
    return build_foundation(
        FoundationConfig(
            kind,
            vocab_size=vocab_size,
            embedding_width=8,
            width=10 if kind == "mingru" else 8,
            layers=2,
            context=64,
            heads=2,
        )
    )


def test_unchanged_utf8_roundtrip_and_fail_closed_boundary(codec):
    text = "Tiếng Việt — state 09:05!"
    assert codec.decode(codec.encode(text, bos=True, eos=True)) == text
    assert codec.encode("!") == [0]
    with pytest.raises(ValueError, match="boundary"):
        codec.response_example("Say: ", "hi")
    encoded = codec.response_example("Say:\n", "hi!")
    assert encoded["targets"][-1] == codec.eos_id
    assert sum(x != -100 for x in encoded["targets"]) == len(codec.encode("hi!")) + 1
    assert encoded["input_ids"][0] == codec.bos_id


def test_lengths_mask_shared_special_token_and_exact_target_cap(codec):
    examples = [codec.response_example("Say:\n", text) for text in ("hi!", "?")]
    batch = make_batch(examples, pad_id=codec.pad_id, context=64, remaining=4)
    assert int((batch["targets"] != -100).sum()) == 4
    assert batch["attention_mask"][:, 0].all()
    assert (batch["targets"][~batch["attention_mask"]] == -100).all()
    assert (batch["input_ids"][~batch["attention_mask"]] == codec.pad_id).all()
    assert codec.eos_id in batch["targets"][0].tolist()


@pytest.mark.parametrize("kind", ["mingru", "transformer"])
def test_dense_cache_step_causality_reset_and_inactive_padding(kind):
    model = model_for(kind).eval()
    ids = torch.tensor([[0, 8, 9, 2, 6, 1], [0, 5, 3, 7, 258, 258]])
    mask = torch.tensor([[1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 0, 0]], dtype=torch.bool)
    with torch.no_grad():
        dense, _ = model(ids, mask)
        cached, _, cached_state = model(ids, mask, return_state=True)
        parts, state = [], None
        for i in range(ids.shape[1]):
            logits, _, state = model(
                ids[:, i : i + 1], mask[:, i : i + 1], state=state, return_state=True
            )
            parts.append(logits)
        torch.testing.assert_close(dense[mask], cached[mask], atol=1e-5, rtol=1e-4)
        torch.testing.assert_close(
            cached[mask], torch.cat(parts, 1)[mask], atol=1e-5, rtol=1e-4
        )
        changed = ids.clone()
        changed[0, -1] = 15
        future, _ = model(changed, mask)
        torch.testing.assert_close(dense[:, :-1], future[:, :-1], atol=0, rtol=0)
        reset, _ = model(ids, mask)
        torch.testing.assert_close(dense, reset, equal_nan=True, atol=0, rtol=0)
        if kind == "mingru":
            _, _, short = model(ids[1:2, :4], return_state=True)
            for last, expected in zip(cached_state["cells"], short["cells"]):
                torch.testing.assert_close(last[1:2], expected)


@pytest.mark.parametrize("kind", ["mingru", "transformer"])
def test_selected_head_loss_and_gradients_equal_dense_masked_loss(codec, kind):
    model = model_for(kind).train()
    batch = make_batch(
        [codec.response_example("Say:\n", s) for s in ("hi!", "?")],
        pad_id=codec.pad_id,
        context=64,
    )
    dense, _ = model(batch["input_ids"], batch["attention_mask"])
    loss = torch.nn.functional.cross_entropy(
        dense.flatten(0, 1), batch["targets"].flatten(), ignore_index=-100
    )
    loss.backward()
    expected = {k: p.grad.clone() for k, p in model.named_parameters()}
    model.zero_grad(set_to_none=True)
    selected, count = selected_ce(model, batch)
    selected.backward()
    assert count == int((batch["targets"] != -100).sum())
    torch.testing.assert_close(loss, selected)
    for key, p in model.named_parameters():
        torch.testing.assert_close(p.grad, expected[key], atol=1e-5, rtol=1e-4)


def test_lexical_initialization_shared_and_zero_id_not_frozen():
    a, b = model_for("mingru"), model_for("transformer")
    assert torch.equal(a.embedding.weight, b.embedding.weight)
    for model in (a, b):
        assert model.head.weight is model.embedding.weight
        assert model.embedding.padding_idx is None
        model.embedding(torch.tensor([0])).sum().backward()
        assert model.embedding.weight.grad[0].abs().sum() > 0
    assert not torch.equal(
        b.blocks.layers[0].linear1.weight, b.blocks.layers[1].linear1.weight
    )
    assert not torch.equal(
        b.blocks.layers[0].self_attn.in_proj_weight,
        b.blocks.layers[1].self_attn.in_proj_weight,
    )


def test_generation_does_not_suppress_eos_when_all_special_ids_are_shared(codec):
    class CertainEOS(torch.nn.Module):
        config = type("Config", (), {"context": 64})()

        def forward(self, ids, **kwargs):
            logits = torch.full((*ids.shape, 259), -100.0)
            logits[..., codec.eos_id] = 100
            return logits, None, None

    result = generate(CertainEOS(), codec, "hi", max_new_tokens=10, top_k=1)
    assert result["eos_emitted"] is True
    assert result["cap_reached"] is False
    assert result["token_ids"] == []


def test_real_preflight_uses_the_common_cached_model_contract():
    import importlib.util
    import sys
    from dataclasses import asdict
    from pathlib import Path

    scripts = Path(__file__).resolve().parents[1] / "scripts"
    sys.path.insert(0, str(scripts))
    try:
        spec = importlib.util.spec_from_file_location(
            "foundation_driver", scripts / "run_q3a_foundation.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    models = {}
    for kind in ("mingru", "transformer"):
        model = model_for(kind)
        cfg = model.foundation_config if kind == "transformer" else model.config
        models[kind] = {"config": asdict(cfg)}
    plan = {
        "plan_id": "fixture",
        "config": {"context": 64},
        "tokenizer_spec": {"vocab_size": 259, "bos_id": 258},
        "models": models,
    }
    check = module.paths_preflight(plan, "cpu", lengths=(8, 16))
    assert check["optimizer_updates"] == 0 and len(check["cases"]) == 4
    assert all(r["past_logit_error"] == 0 for r in check["cases"])


def test_trimmed_edit_distance_agrees_with_full_dynamic_program():
    rng = random.Random(42)
    for _ in range(100):
        a = [rng.randrange(4) for _ in range(rng.randrange(15))]
        b = [rng.randrange(4) for _ in range(rng.randrange(15))]
        table = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
        for i in range(len(a) + 1):
            table[i][0] = i
        for j in range(len(b) + 1):
            table[0][j] = j
        for i in range(1, len(a) + 1):
            for j in range(1, len(b) + 1):
                table[i][j] = min(
                    table[i - 1][j] + 1,
                    table[i][j - 1] + 1,
                    table[i - 1][j - 1] + (a[i - 1] != b[j - 1]),
                )
        assert edit_distance(a, b) == table[-1][-1]


def corpus_fixture(path, rows):
    write_rows(path, rows)
    write_json(
        str(path) + ".manifest.json",
        {
            "sha256": sha256(path),
            "dataset": "unit-fixture",
            "license": "fixture-only",
            "revision": "unit-fixture",
            "source": "generated unit test",
            "stream_shuffle_seed": 1,
        },
    )


def test_normalized_expansion_preserves_all_old_rows_and_excludes_heldouts(tmp_path):
    old = [
        {"source_id": split, "split": split, "text": text}
        for split, text in [
            ("train", "An old story."),
            ("validation", "A held out story."),
            ("test", "Another held out story."),
        ]
    ]
    original, expanded = tmp_path / "old.jsonl", tmp_path / "expanded.jsonl"
    corpus_fixture(original, old)
    stream = [
        {"text": text}
        for text in [" A HELD  OUT STORY. ", "AN OLD STORY.", "A new training story."]
    ]
    manifest = expand_normalized(original, expanded, train_stories=2, stream=stream)
    result = read_rows(expanded)
    assert result[: len(old)] == old
    assert len(result) == 4 and result[-1]["split"] == "train"
    assert manifest["normalized_exclusion"]["skipped_new_candidates"] == 2


def test_long_story_windows_cover_every_target_exactly_once():
    ids = [258, *range(25), 258]
    labels = [
        label
        for start, length in language_windows(ids, 7)
        for label in ids[start + 1 : start + length + 1]
    ]
    assert labels == ids[1:]


def test_encoded_corpus_masks_sft_and_never_encodes_test(codec, tmp_path):
    story = "Lan had a key. Mai kept it safe. The door was red. Huy went back home. They all felt happy."
    rows = [
        {"source_id": "train", "split": "train", "text": story * 8},
        {"source_id": "validation", "split": "validation", "text": story},
        {
            "source_id": "test",
            "split": "test",
            "text": "Do not encode this test source.",
        },
    ]
    original = tmp_path / "original.jsonl"
    corpus_fixture(original, rows)
    encode = codec.encode

    def guarded(text, **kwargs):
        assert text != rows[2]["text"]
        return encode(text, **kwargs)

    codec.encode = guarded
    out = tmp_path / "tokens"
    manifest = encode_corpus(original, out, codec, context=256)
    assert manifest["test_tokenized"] is False
    assert manifest["long_lm_documents_dropped"] == 0
    lm = TokenDataset(out, "train", "lm")
    reconstructed = [label for i in range(len(lm)) for label in lm[i]["targets"]]
    assert reconstructed == encode(rows[0]["text"], eos=True)
    sft = TokenDataset(out, "train", "sft")
    assert len(sft) == 2
    assert all(sft[i]["targets"][-1] == codec.eos_id for i in range(len(sft)))
    assert all(-100 in sft[i]["targets"] for i in range(len(sft)))
    assert set(manifest["splits"]) == {
        "train-lm",
        "train-sft",
        "validation-lm",
        "validation-sft",
    }
    bad = tmp_path / "corrupt-copy"
    shutil.copytree(out, bad)
    with (bad / "train-lm.ids.u16").open("r+b") as f:
        f.write(b"XX")
    with pytest.raises(ValueError, match="manifest"):
        TokenDataset(bad, "train", "lm")
