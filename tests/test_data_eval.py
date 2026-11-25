import json

import pytest

from mim_llm.benchmark import make_pair, write_demo_corpus
from mim_llm.data import StoryDataset, collate, load_jsonl, stable_split
from mim_llm.evaluation import (
    aggregate_labels,
    lock_benchmark,
    make_blind_packet,
    write_jsonl,
)
from mim_llm.oracle import delayed_power, execute_cabinet
from mim_llm.tokenizer import ByteTokenizer, SentencePieceTokenizer
from mim_llm.tokenizer_train import train_tokenizer
from mim_llm.train import file_sha256, load_checkpoint_tokenizer


def test_paired_premise_only_changes_one_time():
    early, late = make_pair(5)
    assert early["prompt"].replace("8:55", "9:05") == late["prompt"]
    assert early["facts_preserved"] == late["facts_preserved"]
    assert early["actual_obligations"][0]["value"] is True
    assert late["actual_obligations"][0]["value"] is False
    assert early["source_id"] == late["source_id"]
    assert execute_cabinet(["Lan", "Huy", "Mai"], "8:55").opened_at_0900
    assert not execute_cabinet(
        ["Lan", "Huy", "Mai"], delayed_power("8:55")
    ).opened_at_0900


def test_story_level_split_and_shift(tmp_path):
    path = tmp_path / "demo.jsonl"
    write_demo_corpus(path, stories=100)
    rows = load_jsonl(path)
    tokenizer = ByteTokenizer()
    for split in ("train", "validation", "test"):
        assert any(row["split"] == split for row in rows)
        dataset = StoryDataset(rows, tokenizer, split, 12)
        assert dataset
        batch = collate([dataset[0], dataset[1]])
        first = dataset[0][0]
        assert batch["input_ids"][0, 0] == first[0]
        assert batch["targets"][0, 0] == first[1]
        assert int(batch["attention_mask"].sum()) == sum(
            len(dataset[i][0]) - 1 for i in (0, 1)
        )
    assert all(row["split"] == stable_split(row["source_id"]) for row in rows)


def test_utf8_tokenizer_roundtrip():
    tokenizer = ByteTokenizer()
    text = "Lan cầm chìa khóa."
    assert tokenizer.decode(tokenizer.encode(text, bos=True, eos=True)) == text


@pytest.mark.training
def test_bpe_state_alignment_and_no_validation_fit(tmp_path):
    path = tmp_path / "demo.jsonl"
    write_demo_corpus(path, stories=30)
    model_file = tmp_path / "sp.model"
    metadata = train_tokenizer(str(path), str(model_file), vocab_size=512)
    rows = load_jsonl(path)
    assert metadata["train_stories"] == sum(row["split"] == "train" for row in rows)
    tokenizer = SentencePieceTokenizer(model_file)
    row = rows[0]
    assert tokenizer.decode(tokenizer.encode(row["text"])) == row["text"]
    aligned = tokenizer.align_byte_labels(row["text"], row["state_labels"])
    assert aligned[-2] == row["state_labels"][-2]
    assert len(aligned) == len(tokenizer.encode(row["text"], bos=True, eos=True))
    assert StoryDataset(rows, tokenizer, row["split"], 128)


def test_benchmark_lock_detects_change(tmp_path):
    from mim_llm.benchmark import write_benchmark

    path, lock_path = tmp_path / "bench.jsonl", tmp_path / "bench.lock.json"
    write_benchmark(path, pairs=4)
    lock = lock_benchmark(str(path), str(lock_path))
    assert lock["pairs"] == 4
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    rows[0]["actual_obligations"][0]["value"] = False
    write_jsonl(path, rows)
    with pytest.raises(ValueError):
        lock_benchmark(str(path), str(lock_path))


def test_benchmark_lock_rejects_source_crossing_splits(tmp_path):
    from mim_llm.benchmark import write_benchmark

    path = tmp_path / "bench.jsonl"
    write_benchmark(path, pairs=2)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    rows[2]["source_id"] = rows[0]["source_id"]
    rows[2]["split"] = "validation" if rows[0]["split"] != "validation" else "test"
    write_jsonl(path, rows)
    with pytest.raises(ValueError, match="crosses benchmark splits"):
        lock_benchmark(str(path), str(tmp_path / "lock.json"))


@pytest.mark.training
def test_checkpoint_tokenizer_hash_is_enforced(tmp_path):
    corpus = tmp_path / "corpus.jsonl"
    write_demo_corpus(corpus, stories=30)
    tokenizer_file = tmp_path / "tokenizer.model"
    train_tokenizer(str(corpus), str(tokenizer_file), vocab_size=512)
    checkpoint_file = tmp_path / "best.pt"
    checkpoint = {
        "config": {"vocab_size": SentencePieceTokenizer(tokenizer_file).vocab_size},
        "tokenizer_sha256": file_sha256(tokenizer_file),
    }
    assert load_checkpoint_tokenizer(checkpoint_file, checkpoint).vocab_size == 512
    tokenizer_file.write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed tokenizer"):
        load_checkpoint_tokenizer(checkpoint_file, checkpoint)


def test_blind_packet_requires_real_labels(tmp_path):
    fields = {
        "pair_id": "pair-1",
        "source_id": "pair-1",
        "id": "row-1",
        "prompt": "A",
        "continuation": "B",
        "obligations": {},
        "model_kind": "mim",
    }
    path_a, path_b = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    write_jsonl(path_a, [fields])
    write_jsonl(path_b, [{**fields, "model_kind": "lstm"}])
    packet, key = tmp_path / "packet.jsonl", tmp_path / "key.jsonl"
    make_blind_packet([str(path_a), str(path_b)], str(packet), str(key))
    with pytest.raises(ValueError, match="Missing adjudicated"):
        aggregate_labels(str(packet), str(key), bootstrap_draws=100)


def test_aggregation_clusters_multiple_pairs_from_one_source(tmp_path):
    key, labels = [], []
    for source, pair in (
        ("story-a", "pair-1"),
        ("story-a", "pair-2"),
        ("story-b", "pair-3"),
    ):
        for condition in ("base", "perturbed"):
            anonymous_id = f"{pair}-{condition}"
            key.append(
                {
                    "anonymous_id": anonymous_id,
                    "system_id": "fixture-system",
                    "source_id": source,
                    "pair_id": pair,
                }
            )
            labels.append(
                {
                    "anonymous_id": anonymous_id,
                    "all_required": True,
                    "contradiction": False,
                    "concrete_event": True,
                    "sentence_count_ok": True,
                    "counterfactual_correct": True,
                    "invariant_correct": True,
                    "fluency_1_to_5": 5,
                    "coverage_0_to_1": 1.0,
                }
            )
    key_path, labels_path = tmp_path / "key.jsonl", tmp_path / "labels.jsonl"
    write_jsonl(key_path, key)
    write_jsonl(labels_path, labels)
    result = aggregate_labels(str(labels_path), str(key_path), bootstrap_draws=100)[
        "fixture-system"
    ]
    assert result["source_stories"] == 2
    assert result["pairs"] == 3
    assert result["point"]["pair_success"] == 1.0
