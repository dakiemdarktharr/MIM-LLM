"""Parameter matching and a conditional four-study experiment map."""

from __future__ import annotations

from dataclasses import asdict, replace
from typing import Any

from .models import ModelConfig, build_model, parameter_count

PAPER_TRACKS: dict[str, dict[str, Any]] = {'q3_counterfactual_training': {'question': 'Do semantic no-op pairs improve selective '
                                            'continuation beyond matched lexical controls?',
                                'required': ['effective/no-op pairs',
                                             'matched paraphrase control',
                                             'published invariance adaptation',
                                             'held-out source transfer',
                                             'blind labels and evasion audit'],
                                'primary_contrast': 'A1 minus A2',
                                'post_training_runs': 24,
                                'pilot_post_targets': 48000000,
                                'stop_or_merge': 'Stop or redesign if gains are template-only '
                                                 'or explained by exposure/quality.'},
 'q3_delayed_supervision': {'question': 'Does semantic-write interference in delayed '
                                        'supervision transfer to generation beyond token '
                                        'delay and QA format?',
                            'required': ['immediate/low-write/high-write/mixed schedules',
                                         'matched answer labels',
                                         'disposable probes',
                                         'measured prefix replay cost',
                                         'continuation transfer'],
                            'primary_contrast': 'B2 minus B1',
                            'post_training_runs': 24,
                            'pilot_post_targets': 48000000,
                            'stop_or_merge': 'Stop or redesign if only probe accuracy changes '
                                             'or timing/compute confounds remain.'},
 'q3_history_provenance': {'question': 'Does frozen self-origin history outperform matched '
                                       'peer-origin history for actual-event consistency?',
                           'required': ['frozen provenance banks',
                                        'teacher/peer/self/mixed arms',
                                        'quality, event and frozen-learner surprisal matching',
                                        'parse/rejection yield',
                                        'free-run and fixed-history panels'],
                           'primary_contrast': 'C2 minus C1',
                           'post_training_runs': 24,
                           'pilot_post_targets': 48000000,
                           'stop_or_merge': 'Stop or redesign if history quality/selection '
                                            'explains the effect.'},
 'q1_branch_residual_memory': {'question': 'Do shared-fork persistent residual states improve '
                                           'the multi-world memory-quality frontier beyond '
                                           'full copies and strong controls?',
                               'required': ['novelty versus SEED/TreeWY/Flide/DASC/MoDr',
                                            'full causal state/router contract',
                                            'full-copy and same-byte baselines',
                                            'pair and N/S controls',
                                            'modern recurrence',
                                            'fresh multi-domain/scaling evidence'],
                               'plan_status': 'candidate architecture, not implemented; '
                                              'actual candidate parameters unknown',
                               'stop_or_merge': 'Do not claim architectural novelty if only '
                                                'cache reuse, oracle routing or a combination '
                                                'of prior components explains it.'}}


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
