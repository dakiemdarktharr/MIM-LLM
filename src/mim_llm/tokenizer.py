"""Deterministic byte tokenizer for every baseline and every split.

The deliberately small vocabulary makes the first pilot auditable. A learned
tokenizer may be added later, but must be fitted on training data only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class ByteTokenizer:
    pad_id = 0
    bos_id = 1
    eos_id = 2
    vocab_size = 259

    def encode(self, text: str, *, bos: bool = False, eos: bool = False) -> list[int]:
        ids = [byte + 3 for byte in text.encode("utf-8")]
        return ([self.bos_id] if bos else []) + ids + ([self.eos_id] if eos else [])

    def decode(self, ids: list[int], *, errors: str = "replace") -> str:
        data = bytes(token - 3 for token in ids if 3 <= token < self.vocab_size)
        return data.decode("utf-8", errors=errors)

    def align_byte_labels(self, text: str, labels: list[int]) -> list[int]:
        if len(labels) != len(text.encode("utf-8")) + 2:
            raise ValueError("Byte labels must include BOS and EOS")
        return labels


class Tokenizer(Protocol):
    pad_id: int
    bos_id: int
    eos_id: int
    vocab_size: int

    def encode(
        self, text: str, *, bos: bool = False, eos: bool = False
    ) -> list[int]: ...
    def decode(self, ids: list[int], *, errors: str = "replace") -> str: ...
    def align_byte_labels(self, text: str, labels: list[int]) -> list[int]: ...


class SentencePieceTokenizer:
    """Train-only fitted BPE, with byte fallback and fixed special IDs."""

    pad_id = 0
    bos_id = 1
    eos_id = 2

    def __init__(self, model_file: str | Path) -> None:
        import sentencepiece as spm

        self.model_file = Path(model_file)
        self.processor = spm.SentencePieceProcessor(model_file=str(self.model_file))
        self.vocab_size = self.processor.vocab_size()
        if (
            self.processor.pad_id(),
            self.processor.bos_id(),
            self.processor.eos_id(),
        ) != (0, 1, 2):
            raise ValueError("Unexpected SentencePiece special token IDs")

    def encode(self, text: str, *, bos: bool = False, eos: bool = False) -> list[int]:
        ids = self.processor.encode(text, out_type=int)
        return ([self.bos_id] if bos else []) + ids + ([self.eos_id] if eos else [])

    def decode(self, ids: list[int], *, errors: str = "replace") -> str:
        return self.processor.decode(
            [
                token
                for token in ids
                if token not in {self.pad_id, self.bos_id, self.eos_id}
            ]
        )

    def align_byte_labels(self, text: str, labels: list[int]) -> list[int]:
        if len(labels) != len(text.encode("utf-8")) + 2:
            raise ValueError("Byte labels must include BOS and EOS")
        pieces = self.processor.encode(text, return_type="proto").pieces
        result = [labels[0]] + [labels[piece.end] for piece in pieces] + [labels[-1]]
        if len(result) != len(self.encode(text, bos=True, eos=True)):
            raise AssertionError("SentencePiece offset alignment failed")
        return result


def load_tokenizer(model_file: str | Path | None = None) -> Tokenizer:
    return (
        SentencePieceTokenizer(model_file)
        if model_file is not None
        else ByteTokenizer()
    )
