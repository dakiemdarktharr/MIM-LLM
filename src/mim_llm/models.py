"""Autoregressive baselines and a vector adaptation of Wang et al.'s MIM.

Original MIM is a convolutional video predictor. These linear cells are an
explicit language-model *variant*, not a line-for-line reproduction. All
recurrent models expose the same forward/step contract for causal checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch
from torch import Tensor, nn
from torch.nn import functional as F


@dataclass(frozen=True)
class ModelConfig:
    kind: str = "mim"
    vocab_size: int = 259
    width: int = 192
    layers: int = 2
    dropout: float = 0.0
    context: int = 256
    state_classes: int = 0
    mim_memory: bool = True
    difference_mode: str = "direct"

    def __post_init__(self) -> None:
        if self.width < 8 or self.layers < 1 or self.vocab_size < 4:
            raise ValueError("Invalid model dimensions")
        if self.kind.startswith("mim") and self.layers < 2:
            raise ValueError("MIM requires one ST layer and at least one MIM layer")
        if not 0 <= self.dropout < 1 or self.context < 2:
            raise ValueError("Invalid dropout or context")
        if self.kind not in {
            "mim",
            "mim_no_n",
            "mim_no_s",
            "mim_no_m",
            "mim_pair",
            "lstm",
            "nested_lstm",
            "gru",
            "mingru",
            "delta_rnn",
            "transformer",
            "token_shift",
        }:
            raise ValueError(f"Unknown model kind: {self.kind}")
        if self.difference_mode not in {"direct", "cascade"}:
            raise ValueError("difference_mode must be direct or cascade")


def _blend(old: Tensor | None, new: Tensor, active: Tensor | None) -> Tensor:
    if old is None or active is None:
        return new
    return torch.where(active[:, None], new, old)


class STCell(nn.Module):
    """Vector ST-LSTM analogue for the first MIM layer.

    C is temporal memory; M is an additional layerwise/stepwise memory.
    """

    def __init__(self, width: int, *, use_memory: bool = True) -> None:
        super().__init__()
        self.use_memory = use_memory
        self.temporal = nn.Linear(width * 2, width * 3)
        if use_memory:
            self.spatial = nn.Linear(width * 2, width * 3)
            self.output = nn.Linear(width * 2, width)
            self.output_gate = nn.Linear(width * 4, width)
        else:
            self.output = nn.Linear(width, width)
            self.output_gate = nn.Linear(width * 3, width)

    def forward(
        self, x: Tensor, state: tuple[Tensor, Tensor, Tensor], incoming_m: Tensor
    ) -> tuple[Tensor, tuple[Tensor, Tensor, Tensor]]:
        h, c, m = state
        i, f, g = self.temporal(torch.cat((x, h), dim=-1)).chunk(3, dim=-1)
        c = torch.sigmoid(f) * c + torch.sigmoid(i) * torch.tanh(g)
        if self.use_memory:
            mi, mf, mg = self.spatial(torch.cat((x, incoming_m), dim=-1)).chunk(
                3, dim=-1
            )
            m = torch.sigmoid(mf) * incoming_m + torch.sigmoid(mi) * torch.tanh(mg)
            combined = torch.cat((c, m), dim=-1)
            o_input = torch.cat((x, h, c, m), dim=-1)
        else:
            m = incoming_m
            combined = c
            o_input = torch.cat((x, h, c), dim=-1)
        h = torch.sigmoid(self.output_gate(o_input)) * torch.tanh(self.output(combined))
        return h, (h, c, m)


class MIMCell(nn.Module):
    """Vector MIM-N -> MIM-S -> C cell.

    `signal` is a lower-layer hidden-state difference, or a learned
    projection of the two states for the information-matched pair control.
    """

    def __init__(
        self,
        width: int,
        *,
        use_n: bool = True,
        use_s: bool = True,
        use_memory: bool = True,
    ) -> None:
        super().__init__()
        self.use_n, self.use_s, self.use_memory = use_n, use_s, use_memory
        self.n_gates = nn.Linear(width * 2, width * 3) if use_n else None
        self.n_output = nn.Linear(width * 2, width) if use_n else None
        self.s_gates = nn.Linear(width * 2, width * 3) if use_s else None
        self.s_output = nn.Linear(width * 3, width) if use_s else None
        self.direct_d = nn.Linear(width, width) if not use_n else None
        self.direct_t = nn.Linear(width * 2, width) if not use_s else None
        self.c_gates = nn.Linear(width * 2, width * 2)
        if use_memory:
            self.m_gates = nn.Linear(width * 2, width * 3)
            self.output = nn.Linear(width * 2, width)
            self.o_gate = nn.Linear(width * 4, width)
        else:
            self.output = nn.Linear(width, width)
            self.o_gate = nn.Linear(width * 3, width)

    def forward(
        self,
        x: Tensor,
        signal: Tensor,
        state: tuple[Tensor, Tensor, Tensor, Tensor, Tensor],
        incoming_m: Tensor,
    ) -> tuple[Tensor, tuple[Tensor, Tensor, Tensor, Tensor, Tensor], Tensor]:
        h, c, m, n, s = state
        if self.use_n:
            ni, nf, ng = self.n_gates(torch.cat((signal, n), dim=-1)).chunk(3, dim=-1)
            n = torch.sigmoid(nf) * n + torch.sigmoid(ni) * torch.tanh(ng)
            d = torch.sigmoid(
                self.n_output(torch.cat((signal, n), dim=-1))
            ) * torch.tanh(n)
        else:
            d = torch.tanh(self.direct_d(signal))
        if self.use_s:
            si, sf, sg = self.s_gates(torch.cat((d, c), dim=-1)).chunk(3, dim=-1)
            s = torch.sigmoid(sf) * s + torch.sigmoid(si) * torch.tanh(sg)
            t = torch.sigmoid(self.s_output(torch.cat((d, c, s), dim=-1))) * torch.tanh(
                s
            )
        else:
            t = torch.tanh(self.direct_t(torch.cat((d, c), dim=-1)))
        ci, cg = self.c_gates(torch.cat((x, h), dim=-1)).chunk(2, dim=-1)
        c = t + torch.sigmoid(ci) * torch.tanh(cg)
        if self.use_memory:
            mi, mf, mg = self.m_gates(torch.cat((x, incoming_m), dim=-1)).chunk(
                3, dim=-1
            )
            m = torch.sigmoid(mf) * incoming_m + torch.sigmoid(mi) * torch.tanh(mg)
            combined = torch.cat((c, m), dim=-1)
            o_input = torch.cat((x, h, c, m), dim=-1)
        else:
            m = incoming_m
            combined = c
            o_input = torch.cat((x, h, c), dim=-1)
        o = torch.sigmoid(self.o_gate(o_input))
        h = o * torch.tanh(self.output(combined))
        return h, (h, c, m, n, s), d


class NestedLSTMCell(nn.Module):
    """Nested LSTM: inner LSTM transforms outer cell update (Moniz & Krueger)."""

    def __init__(self, width: int) -> None:
        super().__init__()
        self.outer = nn.Linear(width * 2, width * 4)
        self.inner = nn.LSTMCell(width, width)

    def forward(
        self, x: Tensor, state: tuple[Tensor, Tensor, Tensor]
    ) -> tuple[Tensor, tuple[Tensor, Tensor, Tensor]]:
        h, c, ic = state
        i, f, g, o = self.outer(torch.cat((x, h), dim=-1)).chunk(4, dim=-1)
        # Moniz & Krueger (2017), Eqs. 7-15: the inner LSTM sees the
        # input-gated candidate and forget-gated *outer* cell as its hidden
        # state, while its own cell memory persists across time.
        inner_input = torch.sigmoid(i) * g
        inner_hidden = torch.sigmoid(f) * c
        ih, ic = self.inner(inner_input, (inner_hidden, ic))
        c = ih
        h = torch.sigmoid(o) * torch.tanh(c)
        return h, (h, c, ic)


class MinGRUCell(nn.Module):
    """Input-only minGRU gates and linear candidate (Feng et al., 2024)."""

    def __init__(self, width: int) -> None:
        super().__init__()
        self.projection = nn.Linear(width, width * 2)

    def forward(self, x: Tensor, h: Tensor) -> tuple[Tensor, Tensor]:
        z, candidate = self.projection(x).chunk(2, dim=-1)
        z = torch.sigmoid(z)
        h = (1 - z) * h + z * candidate
        return h, h


def _affine_prefix_scan(a: Tensor, b: Tensor) -> Tensor:
    """Associative scan for h_t = a_t * h_(t-1) + b_t."""
    offset = 1
    while offset < a.shape[1]:
        old_a, old_b = a, b
        a = torch.cat(
            (old_a[:, :offset], old_a[:, offset:] * old_a[:, :-offset]), dim=1
        )
        b = torch.cat(
            (
                old_b[:, :offset],
                old_b[:, offset:] + old_a[:, offset:] * old_b[:, :-offset],
            ),
            dim=1,
        )
        offset *= 2
    return b


class DeltaRNNCell(nn.Module):
    """Late-integration second-order Delta-RNN (Ororbia et al., 2017).

    Its 'delta' is an implicit gated update; it does not feed h_t-h_(t-1)
    into MIM-N. This baseline tests the nearby LM design directly.
    """

    def __init__(self, width: int) -> None:
        super().__init__()
        self.input = nn.Linear(width, width, bias=False)
        self.recurrent = nn.Linear(width, width, bias=False)
        self.gate_bias = nn.Parameter(torch.zeros(width))
        self.alpha = nn.Parameter(torch.ones(width))
        self.beta_input = nn.Parameter(torch.ones(width))
        self.beta_recurrent = nn.Parameter(torch.ones(width))
        self.bias = nn.Parameter(torch.zeros(width))

    def forward(self, x: Tensor, h: Tensor) -> tuple[Tensor, Tensor]:
        projected_x = self.input(x)
        projected_h = self.recurrent(h)
        z = torch.tanh(
            self.alpha * projected_x * projected_h
            + self.beta_input * projected_x
            + self.beta_recurrent * projected_h
            + self.bias
        )
        r = torch.sigmoid(projected_x + self.gate_bias)
        h = (1 - r) * z + r * h
        return h, h


class RecurrentLM(nn.Module):
    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self.config = config
        w = config.width
        self.embedding = nn.Embedding(config.vocab_size, w, padding_idx=0)
        self.kind = config.kind
        self.input_dropout = nn.Dropout(config.dropout)
        self.output_dropout = nn.Dropout(config.dropout)
        self.cells = nn.ModuleList()
        if config.kind.startswith("mim"):
            self.cells.append(
                STCell(w, use_memory=config.mim_memory and config.kind != "mim_no_m")
            )
            for _ in range(config.layers - 1):
                self.cells.append(
                    MIMCell(
                        w,
                        use_n=config.kind != "mim_no_n",
                        use_s=config.kind != "mim_no_s",
                        use_memory=config.mim_memory and config.kind != "mim_no_m",
                    )
                )
            self.pair = nn.Linear(w * 2, w) if config.kind == "mim_pair" else None
        elif config.kind == "lstm":
            self.cells.extend(nn.LSTMCell(w, w) for _ in range(config.layers))
        elif config.kind == "nested_lstm":
            self.cells.extend(NestedLSTMCell(w) for _ in range(config.layers))
        elif config.kind == "gru":
            self.cells.extend(nn.GRUCell(w, w) for _ in range(config.layers))
        elif config.kind == "mingru":
            self.cells.extend(MinGRUCell(w) for _ in range(config.layers))
        elif config.kind == "delta_rnn":
            self.cells.extend(DeltaRNNCell(w) for _ in range(config.layers))
        elif config.kind == "token_shift":
            self.shift = nn.Linear(w * 2, w)
            self.cells.extend(nn.GRUCell(w, w) for _ in range(config.layers))
        self.norm = nn.LayerNorm(w)
        self.head = nn.Linear(w, config.vocab_size, bias=False)
        self.state_head = (
            nn.Linear(w, config.state_classes) if config.state_classes else None
        )

    def initial_state(
        self, batch: int, *, device: torch.device, dtype: torch.dtype
    ) -> dict[str, Any]:
        z = lambda: torch.zeros(batch, self.config.width, device=device, dtype=dtype)
        if self.kind.startswith("mim"):
            cells = [(z(), z(), z())] + [
                (z(), z(), z(), z(), z()) for _ in range(self.config.layers - 1)
            ]
            return {
                "cells": cells,
                "lower_prev": [z() for _ in range(self.config.layers - 1)],
                "top_m": z(),
                "has_prev": torch.zeros(batch, dtype=torch.bool, device=device),
            }
        if self.kind in {"lstm", "nested_lstm"}:
            size = 3 if self.kind == "nested_lstm" else 2
            cells = [tuple(z() for _ in range(size)) for _ in range(self.config.layers)]
        else:
            cells = [z() for _ in range(self.config.layers)]
        return {"cells": cells, "prev_embedding": z()}

    def step(
        self,
        token: Tensor,
        state: dict[str, Any] | None = None,
        active: Tensor | None = None,
    ) -> tuple[Tensor, dict[str, Any], Tensor | None]:
        if token.ndim != 1:
            raise ValueError("step requires [batch] token IDs")
        x = self.input_dropout(self.embedding(token))
        if state is None:
            state = self.initial_state(
                token.shape[0], device=token.device, dtype=x.dtype
            )
        old_cells = state["cells"]
        new_cells = []
        lower_prev = []
        if self.kind.startswith("mim"):
            incoming_m = state["top_m"]
            previous_d = None
            for layer, cell in enumerate(self.cells):
                lower = x
                if layer == 0:
                    y, proposal = cell(x, old_cells[layer], incoming_m)
                else:
                    previous = state["lower_prev"][layer - 1]
                    if self.config.difference_mode == "cascade" and layer > 1:
                        signal = previous_d
                    else:
                        signal = (
                            self.pair(torch.cat((lower, previous), dim=-1))
                            if self.pair is not None
                            else lower - previous
                        )
                    signal = torch.where(
                        state["has_prev"][:, None], signal, torch.zeros_like(signal)
                    )
                    y, proposal, previous_d = cell(
                        x, signal, old_cells[layer], incoming_m
                    )
                    lower_prev.append(lower)
                new_cells.append(
                    tuple(
                        _blend(old, new, active)
                        for old, new in zip(old_cells[layer], proposal)
                    )
                )
                incoming_m = new_cells[-1][2]
                x = _blend(old_cells[layer][0], y, active)
            top_m = _blend(state["top_m"], incoming_m, active)
            has_prev = (
                torch.ones_like(state["has_prev"])
                if active is None
                else (state["has_prev"] | active)
            )
            new_state = {
                "cells": new_cells,
                "lower_prev": [
                    _blend(old, new, active)
                    for old, new in zip(state["lower_prev"], lower_prev)
                ],
                "top_m": top_m,
                "has_prev": has_prev,
            }
        else:
            prev_embedding = state["prev_embedding"]
            if self.kind == "token_shift":
                x = self.shift(torch.cat((x, prev_embedding), dim=-1))
            for layer, cell in enumerate(self.cells):
                if self.kind == "nested_lstm":
                    y, proposal = cell(x, old_cells[layer])
                elif self.kind == "lstm":
                    h, c = cell(x, old_cells[layer])
                    y, proposal = h, (h, c)
                elif self.kind in {"mingru", "delta_rnn"}:
                    y, proposal = cell(x, old_cells[layer])
                else:
                    y = cell(x, old_cells[layer])
                    proposal = y
                if isinstance(proposal, tuple):
                    new_cells.append(
                        tuple(
                            _blend(old, new, active)
                            for old, new in zip(old_cells[layer], proposal)
                        )
                    )
                else:
                    new_cells.append(_blend(old_cells[layer], proposal, active))
                x = _blend(
                    old_cells[layer][0]
                    if isinstance(old_cells[layer], tuple)
                    else old_cells[layer],
                    y,
                    active,
                )
            new_state = {
                "cells": new_cells,
                "prev_embedding": _blend(prev_embedding, self.embedding(token), active),
            }
        features = self.norm(self.output_dropout(x))
        return (
            self.head(features),
            new_state,
            self.state_head(features) if self.state_head else None,
        )

    def forward(
        self,
        input_ids: Tensor,
        attention_mask: Tensor | None = None,
        *,
        state: dict[str, Any] | None = None,
        return_state: bool = False,
    ) -> tuple[Tensor, Tensor | None] | tuple[Tensor, Tensor | None, dict[str, Any]]:
        if input_ids.ndim != 2 or input_ids.shape[1] == 0:
            raise ValueError("input_ids must have shape [batch, time>=1]")
        if self.kind == "mingru":
            return self._forward_mingru_scan(
                input_ids, attention_mask, state=state, return_state=return_state
            )
        logits, states = [], []
        for t in range(input_ids.shape[1]):
            active = attention_mask[:, t].bool() if attention_mask is not None else None
            l, state, s = self.step(input_ids[:, t], state, active)
            logits.append(l)
            if s is not None:
                states.append(s)
        result = (
            torch.stack(logits, dim=1),
            torch.stack(states, dim=1) if states else None,
        )
        return (*result, state) if return_state else result

    def _forward_mingru_scan(
        self,
        input_ids: Tensor,
        attention_mask: Tensor | None,
        *,
        state: dict[str, Any] | None,
        return_state: bool,
    ) -> tuple[Tensor, Tensor | None] | tuple[Tensor, Tensor | None, dict[str, Any]]:
        x = self.input_dropout(self.embedding(input_ids))
        if state is None:
            state = self.initial_state(
                input_ids.shape[0], device=input_ids.device, dtype=x.dtype
            )
        new_cells = []
        for layer, cell in enumerate(self.cells):
            z_logits, candidate = cell.projection(x).chunk(2, dim=-1)
            z = torch.sigmoid(z_logits)
            a, b = 1 - z, z * candidate
            if attention_mask is not None:
                active = attention_mask.bool()[:, :, None]
                a = torch.where(active, a, torch.ones_like(a))
                b = torch.where(active, b, torch.zeros_like(b))
            b = torch.cat(
                (b[:, :1] + a[:, :1] * state["cells"][layer][:, None], b[:, 1:]), dim=1
            )
            x = _affine_prefix_scan(a, b)
            new_cells.append(x[:, -1])
        features = self.norm(self.output_dropout(x))
        result = (
            self.head(features),
            self.state_head(features) if self.state_head else None,
        )
        new_state = {"cells": new_cells, "prev_embedding": state["prev_embedding"]}
        return (*result, new_state) if return_state else result


class TransformerLM(nn.Module):
    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self.config = config
        self.embedding = nn.Embedding(config.vocab_size, config.width, padding_idx=0)
        self.position = nn.Embedding(config.context, config.width)
        encoder_layer = nn.TransformerEncoderLayer(
            config.width,
            nhead=4,
            dim_feedforward=config.width * 4,
            dropout=config.dropout,
            batch_first=True,
            norm_first=True,
        )
        self.blocks = nn.TransformerEncoder(
            encoder_layer, config.layers, enable_nested_tensor=False
        )
        self.norm = nn.LayerNorm(config.width)
        self.head = nn.Linear(config.width, config.vocab_size, bias=False)
        self.state_head = (
            nn.Linear(config.width, config.state_classes)
            if config.state_classes
            else None
        )

    def _cached_eval(
        self,
        input_ids: Tensor,
        attention_mask: Tensor | None,
        state: dict[str, Any] | None,
    ) -> tuple[Tensor, Tensor | None, dict[str, Any]]:
        """Exact causal KV reuse with the existing encoder weights, in eval mode.

        An explicit absolute-position mask is used for chunks with a prefix;
        SDPA's non-square is_causal mask would align differently.
        """
        if input_ids.ndim != 2 or input_ids.shape[1] == 0:
            raise ValueError("Nonempty [batch,time] inputs required")
        batch, time = input_ids.shape
        offset = state["length"] if state is not None else 0
        total = offset + time
        if total > self.config.context:
            raise ValueError("Sequence exceeds Transformer context")
        active = (
            attention_mask.bool()
            if attention_mask is not None
            else torch.ones_like(input_ids, dtype=torch.bool)
        )
        active = (
            torch.cat((state["mask"], active), dim=1) if state is not None else active
        )
        positions = torch.arange(offset, total, device=input_ids.device)
        x = self.embedding(input_ids) + self.position(positions)[None, :, :]
        allowed = (
            torch.arange(total, device=input_ids.device)[None, :] <= positions[:, None]
        )[None, None, :, :]
        allowed = allowed & active[:, None, None, :]
        caches = []
        for index, layer in enumerate(self.blocks.layers):
            norm = layer.norm1(x)
            q, k, v = F.linear(
                norm, layer.self_attn.in_proj_weight, layer.self_attn.in_proj_bias
            ).chunk(3, dim=-1)
            heads = layer.self_attn.num_heads
            dimension = self.config.width // heads
            q = q.reshape(batch, time, heads, dimension).transpose(1, 2)
            k = k.reshape(batch, time, heads, dimension).transpose(1, 2)
            v = v.reshape(batch, time, heads, dimension).transpose(1, 2)
            if state is not None:
                old_k, old_v = state["kv"][index]
                k = torch.cat((old_k, k), dim=2)
                v = torch.cat((old_v, v), dim=2)
            attended = F.scaled_dot_product_attention(
                q, k, v, attn_mask=allowed, dropout_p=0.0
            )
            attended = attended.transpose(1, 2).reshape(batch, time, self.config.width)
            x = x + layer.dropout1(layer.self_attn.out_proj(attended))
            feed = layer.linear2(
                layer.dropout(layer.activation(layer.linear1(layer.norm2(x))))
            )
            x = x + layer.dropout2(feed)
            caches.append((k, v))
        if self.blocks.norm is not None:
            x = self.blocks.norm(x)
        hidden = self.norm(x)
        return (
            self.head(hidden),
            self.state_head(hidden) if self.state_head else None,
            {"kv": caches, "length": total, "mask": active},
        )

    def forward(
        self,
        input_ids: Tensor,
        attention_mask: Tensor | None = None,
        *,
        state: dict[str, Any] | None = None,
        return_state: bool = False,
    ) -> tuple[Tensor, Tensor | None] | tuple[Tensor, Tensor | None, dict[str, Any]]:
        if not self.training and return_state and (state is None or "kv" in state):
            return self._cached_eval(input_ids, attention_mask, state)
        if state is not None and "kv" in state:
            raise ValueError(
                "KV-cached state is supported only for eval with return_state=True"
            )
        if state is not None:
            input_ids = torch.cat((state["tokens"], input_ids), dim=1)
            if attention_mask is not None and state.get("mask") is not None:
                attention_mask = torch.cat((state["mask"], attention_mask), dim=1)
        time = input_ids.shape[1]
        if time > self.config.context:
            raise ValueError(
                f"Sequence exceeds Transformer context {self.config.context}"
            )
        x = (
            self.embedding(input_ids)
            + self.position(torch.arange(time, device=input_ids.device))[None, :, :]
        )
        mask = torch.triu(
            torch.ones(time, time, dtype=torch.bool, device=input_ids.device),
            diagonal=1,
        )
        hidden = self.norm(
            self.blocks(
                x,
                mask=mask,
                src_key_padding_mask=~attention_mask.bool()
                if attention_mask is not None
                else None,
            )
        )
        logits = self.head(hidden)
        state_logits = self.state_head(hidden) if self.state_head else None
        new_state = {"tokens": input_ids, "mask": attention_mask}
        if state is not None:
            old_time = state["tokens"].shape[1]
            logits = logits[:, old_time:]
            state_logits = (
                state_logits[:, old_time:] if state_logits is not None else None
            )
        result = (logits, state_logits)
        return (*result, new_state) if return_state else result


def build_model(config: ModelConfig) -> nn.Module:
    return (
        TransformerLM(config) if config.kind == "transformer" else RecurrentLM(config)
    )


def parameter_count(model: nn.Module) -> int:
    return sum(
        parameter.numel() for parameter in model.parameters() if parameter.requires_grad
    )


def cross_entropy(
    logits: Tensor, targets: Tensor, *, ignore_index: int = -100
) -> Tensor:
    return F.cross_entropy(
        logits.reshape(-1, logits.shape[-1]),
        targets.reshape(-1),
        ignore_index=ignore_index,
    )
