"""Fit SentencePiece only on the training split of a prepared corpus."""

from __future__ import annotations

from pathlib import Path

from .data import load_jsonl
from .tokenizer import SentencePieceTokenizer


def train_tokenizer(
    corpus: str, output_model: str, *, vocab_size: int = 2048
) -> dict[str, object]:
    import sentencepiece as spm

    if vocab_size < 300:
        raise ValueError("byte_fallback requires a vocabulary of at least 300")
    output = Path(output_model)
    if output.suffix != ".model":
        raise ValueError("output_model must end with .model")
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(".train.txt")
    rows = [row for row in load_jsonl(corpus) if row["split"] == "train"]
    if not rows:
        raise ValueError("No training stories")
    try:
        with temp.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(row["text"].replace("\r", " ").replace("\n", " ") + "\n")
        spm.SentencePieceTrainer.train(
            input=str(temp),
            model_prefix=str(output.with_suffix("")),
            model_type="bpe",
            vocab_size=vocab_size,
            byte_fallback=True,
            pad_id=0,
            bos_id=1,
            eos_id=2,
            unk_id=3,
            normalization_rule_name="identity",
            remove_extra_whitespaces=False,
            add_dummy_prefix=False,
            hard_vocab_limit=False,
            minloglevel=2,
        )
    finally:
        temp.unlink(missing_ok=True)
    tokenizer = SentencePieceTokenizer(output)
    return {
        "output_model": str(output.resolve()),
        "actual_vocab_size": tokenizer.vocab_size,
        "train_stories": len(rows),
    }
