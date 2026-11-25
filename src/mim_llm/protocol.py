"""Parameter matching and a fixed four-manuscript experiment map."""

from __future__ import annotations

from dataclasses import asdict, replace
from typing import Any

from .models import ModelConfig, build_model, parameter_count

PAPER_TRACKS: dict[str, dict[str, Any]] = {
    "q3_benchmark": {
        "question": "Does world/time grouping improve evaluator validity beyond a strong information-matched checklist on held-out story continuations?",
        "supports": "q1_architecture: validated task contract, frozen scoring protocol and fresh-source test design",
        "plan_status": "revision 2; evaluator study design, not an implemented evaluator",
        "required": [
            "validated executable obligations",
            "held-out source stories",
            "two blind human readers",
            "inter-rater agreement",
            "generic-evasion audit",
            "strong flat checklist with identical proposition information",
            "primary evaluator delta on unmodified generated prose",
            "paired source-clustered uncertainty and evaluator cost",
        ],
        "stop_or_merge": "Merge into Q1 evaluation if labels, evaluator capability or incremental findings cannot support an independent validity study.",
    },
    "q3_supervision": {
        "supports": "q1_architecture: train-only state-label schema and supervision ablation",
        "question": "Does training-only state supervision improve continuation consistency beyond the same backbone without it?",
        "required": [
            "identical corpus and tokens",
            "state-labelled train split",
            "no gold states during intrinsic inference",
            "multiple seeds",
        ],
        "stop_or_merge": "Merge if supervision effect is too small or depends only on synthetic templates.",
    },
    "q3_mechanisms": {
        "supports": "q1_architecture: N/S/M mechanisms, failure scope and resource-matched controls",
        "question": "Which parts of vector MIM matter per parameter and per unit of compute?",
        "required": [
            "MIM-N/S/M ablations",
            "pair-projection control",
            "Delta-RNN/Nested LSTM",
            "parameter and compute matching",
            "failure analysis",
        ],
        "stop_or_merge": "Merge if the mechanism analysis is only a subset of the architecture paper.",
    },
    "q1_architecture": {
        "question": "Does explicit hidden-state differencing through nested memory generalize to natural story continuation?",
        "required": [
            "natural licensed test stories",
            "strong baselines",
            "multiple seeds",
            "blind human evaluation",
            "resource disclosure",
            "transfer across domains",
        ],
        "stop_or_merge": "Do not submit an architecture claim if the learned-pair control matches or beats it within uncertainty.",
    },
}


def match_width(
    target_parameters: int,
    template: ModelConfig,
    *,
    low: int = 8,
    high: int = 1024,
    multiple: int = 1,
) -> dict[str, Any]:
    if target_parameters < 1 or low < 8 or high < low or multiple < 1:
        raise ValueError("Invalid matching range")
    candidates = range(
        ((low + multiple - 1) // multiple) * multiple, high + 1, multiple
    )
    best = None
    for width in candidates:
        if template.kind == "transformer" and width % 4:
            continue
        config = replace(template, width=width)
        count = parameter_count(build_model(config))
        delta = abs(count - target_parameters)
        if best is None or delta < best[0]:
            best = (delta, width, count)
        # Parameter count rises monotonically with width for these models.
        if count > target_parameters and best is not None:
            break
    if best is None:
        raise ValueError("No compatible width")
    return {
        "config": asdict(replace(template, width=best[1])),
        "target_parameters": target_parameters,
        "actual_parameters": best[2],
        "relative_parameter_gap": (best[2] - target_parameters) / target_parameters,
    }
