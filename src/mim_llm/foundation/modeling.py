"""Tied 64-dimensional lexical heads with separately measured backbone capacity.

Factorized linear-candidate minGRU and a causal GELU Transformer are project
baseline variants. They are not the full original minGRU stack or GPT-Neo.
"""

import math
from dataclasses import dataclass

import torch
from torch import nn

from ..models import MinGRUCell, ModelConfig, TransformerLM, _affine_prefix_scan


@dataclass(frozen=True)
class FoundationConfig:
    kind: str
    vocab_size: int = 50257
    embedding_width: int = 64
    width: int = 325
    layers: int = 2
    context: int = 1024
    heads: int = 4
    dropout: float = 0.0

    def __post_init__(self):
        if self.kind not in {"mingru", "transformer"}:
            raise ValueError("Only the two language-foundation baselines are defined")
        if (
            min(
                self.vocab_size,
                self.embedding_width,
                self.width,
                self.layers,
                self.context,
                self.heads,
            )
            < 1
        ):
            raise ValueError("Invalid model dimensions")
        if self.dropout != 0:
            raise ValueError("This bounded feasibility design requires dropout zero")
        if self.kind == "transformer" and (
            self.width != self.embedding_width or self.width % self.heads
        ):
            raise ValueError("Transformer embedding/hidden width and heads mismatch")


def _init_lexical(model, seed):
    model.head.weight = model.embedding.weight
    model.embedding.padding_idx = None  # GPT-Neo token 0 is valid text, not padding.
    generator = torch.Generator(device="cpu").manual_seed(1_000_000 + seed)
    with torch.no_grad():
        model.embedding.weight.normal_(std=0.02, generator=generator)


def _init_linear(module):
    if isinstance(module, nn.Linear):
        nn.init.normal_(module.weight, std=0.02)
        if module.bias is not None:
            nn.init.zeros_(module.bias)


class FactorizedMinGRU(nn.Module):
    def __init__(self, config, *, lexical_seed=0):
        super().__init__()
        self.config = config
        w, e = config.width, config.embedding_width
        self.embedding = nn.Embedding(config.vocab_size, e)
        self.input_projection = nn.Linear(e, w)
        self.cells = nn.ModuleList(MinGRUCell(w) for _ in range(config.layers))
        self.norm = nn.LayerNorm(w)
        self.output_projection = nn.Linear(w, e)
        self.head = nn.Linear(e, config.vocab_size, bias=False)
        self.apply(_init_linear)
        _init_lexical(self, lexical_seed)

    def _features(self, input_ids, attention_mask=None, state=None):
        x = self.input_projection(self.embedding(input_ids))
        previous = (
            state["cells"]
            if state is not None
            else [x.new_zeros(x.shape[0], self.config.width) for _ in self.cells]
        )
        if len(previous) != len(self.cells):
            raise ValueError("Recurrent state has the wrong layer count")
        cells = []
        for cell, old in zip(self.cells, previous):
            gates, candidate = cell.projection(x).chunk(2, dim=-1)
            z = gates.sigmoid()
            a, b = 1 - z, z * candidate
            if attention_mask is not None:
                active = attention_mask.bool().unsqueeze(-1)
                a = torch.where(active, a, torch.ones_like(a))
                b = torch.where(active, b, torch.zeros_like(b))
            b = torch.cat((b[:, :1] + a[:, :1] * old[:, None], b[:, 1:]), dim=1)
            x = _affine_prefix_scan(a, b)
            cells.append(x[:, -1])
        return self.output_projection(self.norm(x)), {"cells": cells}

    def training_features(self, input_ids, attention_mask=None):
        return self._features(input_ids, attention_mask)[0]

    def forward(
        self, input_ids, attention_mask=None, *, state=None, return_state=False
    ):
        if input_ids.ndim != 2 or input_ids.shape[1] == 0:
            raise ValueError("Nonempty [batch,time] tokens required")
        features, updated = self._features(input_ids, attention_mask, state)
        result = self.head(features), None
        return (*result, updated) if return_state else result

    def step(self, token, state=None, active=None):
        x = self.input_projection(self.embedding(token))
        old = (
            state["cells"]
            if state is not None
            else [torch.zeros_like(x) for _ in self.cells]
        )
        if len(old) != len(self.cells):
            raise ValueError("Recurrent state has the wrong layer count")
        cells = []
        for cell, h in zip(self.cells, old):
            _, proposal = cell(x, h)
            x = (
                proposal
                if active is None
                else torch.where(active[:, None], proposal, h)
            )
            cells.append(x)
        return self.head(self.output_projection(self.norm(x))), {"cells": cells}, None


class TiedTransformer(TransformerLM):
    def __init__(self, config, *, lexical_seed=0):
        # Reuse the verified forward/cache contract, with our own constructor.
        nn.Module.__init__(self)
        self.config = ModelConfig(
            kind="transformer",
            vocab_size=config.vocab_size,
            width=config.width,
            layers=config.layers,
            dropout=0,
            context=config.context,
        )
        self.foundation_config = config
        self.embedding = nn.Embedding(config.vocab_size, config.embedding_width)
        self.position = nn.Embedding(config.context, config.width)
        layer = nn.TransformerEncoderLayer(
            config.width,
            config.heads,
            config.width * 4,
            dropout=0,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.blocks = nn.TransformerEncoder(
            layer, config.layers, enable_nested_tensor=False
        )
        self.norm = nn.LayerNorm(config.width)
        self.head = nn.Linear(config.embedding_width, config.vocab_size, bias=False)
        self.state_head = None
        # Reinitialize every cloned layer independently, including packed QKV.
        self.blocks.apply(_init_linear)
        for layer in self.blocks.layers:
            nn.init.normal_(layer.self_attn.in_proj_weight, std=0.02)
            nn.init.zeros_(layer.self_attn.in_proj_bias)
            std = 0.02 / math.sqrt(2 * config.layers)
            nn.init.normal_(layer.self_attn.out_proj.weight, std=std)
            nn.init.normal_(layer.linear2.weight, std=std)
        nn.init.normal_(self.position.weight, std=0.02)
        _init_lexical(self, lexical_seed)

    def training_features(self, input_ids, attention_mask=None):
        length = input_ids.shape[1]
        if length > self.config.context:
            raise ValueError("Sequence exceeds context")
        x = (
            self.embedding(input_ids)
            + self.position(torch.arange(length, device=input_ids.device))[None]
        )
        mask = torch.ones(
            length, length, device=input_ids.device, dtype=torch.bool
        ).triu(1)
        return self.norm(
            self.blocks(
                x,
                mask=mask,
                src_key_padding_mask=(~attention_mask.bool())
                if attention_mask is not None
                else None,
            )
        )


def build_foundation(config, *, seed=0):
    cls = FactorizedMinGRU if config.kind == "mingru" else TiedTransformer
    return cls(config, lexical_seed=seed)


def parameter_breakdown(model):
    assert model.head.weight is model.embedding.weight
    total = sum(p.numel() for p in model.parameters())
    lexical = model.embedding.weight.numel()
    position = model.position.weight.numel() if hasattr(model, "position") else 0
    return {
        "actual_parameters": total,
        "token_embeddings": lexical,
        "position_embeddings": position,
        "other_parameters": total - lexical - position,
    }
