"""Load an immutable published tokenizer; no training or vocabulary changes."""

import hashlib
from pathlib import Path

from tokenizers import Tokenizer


class FrozenTokenizer:
    def __init__(self, path, spec):
        self.path = Path(path)
        self.spec = dict(spec)
        if hashlib.sha256(self.path.read_bytes()).hexdigest() != spec["sha256"]:
            raise ValueError("Tokenizer bytes differ from declared snapshot")
        self.backend = Tokenizer.from_file(str(self.path))
        if self.backend.padding is not None or self.backend.truncation is not None:
            raise ValueError("Implicit tokenizer padding/truncation is prohibited")
        self.vocab_size = self.backend.get_vocab_size(with_added_tokens=True)
        if self.vocab_size != spec["vocab_size"]:
            raise ValueError("Tokenizer vocabulary changed")
        self.bos_id, self.eos_id, self.pad_id = (
            spec["bos_id"],
            spec["eos_id"],
            spec["pad_id"],
        )
        for name in ("bos", "eos", "pad"):
            if not 0 <= getattr(self, name + "_id") < self.vocab_size:
                raise ValueError("Special token outside vocabulary")
        if self.backend.token_to_id(spec["eos_token"]) != self.eos_id:
            raise ValueError("Wrong end-of-text token identity")

    def encode(self, text, *, bos=False, eos=False):
        ids = self.backend.encode(text, add_special_tokens=False).ids
        return ([self.bos_id] if bos else []) + ids + ([self.eos_id] if eos else [])

    def decode(self, ids, *, skip_special_tokens=True):
        return self.backend.decode(ids, skip_special_tokens=skip_special_tokens)

    def response_example(self, prompt, response):
        """Require a stable generation boundary, e.g. a newline separator.

        Byte-level BPE can merge a prompt's final space with the answer. Fail
        rather than silently train on a different prefix or leak answer tokens.
        """
        if not response:
            raise ValueError("Empty continuation")
        prefix = self.encode(prompt, bos=True)
        suffix = self.encode(response, eos=True)
        complete = self.encode(prompt + response, bos=True, eos=True)
        if prefix + suffix != complete:
            raise ValueError("Unstable prompt-response BPE boundary; use a separator")
        if self.eos_id in prefix[1:] or self.eos_id in suffix[:-1]:
            raise ValueError("Literal reserved token inside story text")
        return {
            "input_ids": complete[:-1],
            "targets": [-100] * (len(prefix) - 1) + suffix,
        }


GPT_NEO_SPEC = {
    "sha256": "f6ed3d307010c244c22aeffbde05f419cf277c23e64cf98b673cac5449cfeff5",
    "vocab_size": 50257,
    "bos_id": 50256,
    "eos_id": 50256,
    "pad_id": 50256,
    "eos_token": "<|endoftext|>",
}
