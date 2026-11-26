"""Held-out general-language NLL/PPL with whole-source uncertainty.

Foundation feasibility may use validation only. General test text remains locked
behind the post-study selection and is evaluated at unscaled full vocabulary.
"""

import json
import math
import random
import time
from collections import defaultdict
from pathlib import Path

import torch
from torch.nn import functional as F

from ..foundation.codec import FrozenTokenizer
from ..foundation.corpus import TokenDataset, language_windows
from ..foundation.modeling import FoundationConfig, build_foundation
from ..foundation.objectives import make_batch
from ..foundation.plan import load_plan as load_foundation_plan
from ..q3a.io import read_rows, sha256, source_sha256
from .evaluate import complete_checkpoint, read_selection
from .foundation_review import check_complete_parent
from .inference import BACKEND
from .plan import load_plan
from .trained_paths import weights_sha256

GENERAL_TEST_POLICY = "all_frozen_general_test_sources_next_token_with_EOS"


def source_interval(rows, *, draws=2000, seed=2026):
    if type(draws) is not int or draws < 100 or not rows:
        raise ValueError("Nonempty sources and at least100 bootstrap draws required")
    rng = random.Random(seed)
    samples = []
    for _ in range(draws):
        selected = rng.choices(rows, k=len(rows))
        samples.append(
            sum(r["nll_sum_nats"] for r in selected)
            / sum(r["targets"] for r in selected)
        )
    samples.sort()
    lower, upper = samples[int(0.025 * (draws - 1))], samples[int(0.975 * (draws - 1))]
    return {
        "nll_ci95": [lower, upper],
        "perplexity_ci95": [math.exp(min(lower, 80)), math.exp(min(upper, 80))],
        "perplexity_ci_clipped": upper > 80,
        "source_clusters": len(rows),
        "draws": draws,
        "seed": seed,
        "scope": "whole-source resampling conditional on this trained checkpoint; not across-training-seed uncertainty",
    }


def heldout_test_examples(corpus, tokenizer, context):
    seen = set()
    with Path(corpus).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["split"] != "test":
                continue
            source = row["source_id"]
            if source in seen or not row["text"].strip():
                raise ValueError("Duplicate/empty held-out general source")
            seen.add(source)
            ids = tokenizer.encode(row["text"], bos=True, eos=True)
            if tokenizer.eos_id in ids[1:-1]:
                raise ValueError("Reserved token inside held-out story")
            for start, length in language_windows(ids, context):
                yield (
                    source,
                    {
                        "input_ids": ids[start : start + length],
                        "targets": ids[start + 1 : start + length + 1],
                    },
                )


@torch.inference_mode()
def summarize_language(
    model, examples, *, pad_id, context, batch_size, device, draws=2000
):
    model.eval()
    by_source = defaultdict(lambda: {"nll_sum_nats": 0.0, "targets": 0, "windows": 0})
    pending = []
    windows = 0

    def consume(items):
        batch = make_batch(
            [x[1] for x in items], pad_id=pad_id, context=context, device=device
        )
        active = batch["targets"] != -100
        features = model.training_features(batch["input_ids"], batch["attention_mask"])
        losses = F.cross_entropy(
            model.head(features[active]), batch["targets"][active], reduction="none"
        )
        if not torch.isfinite(losses).all():
            raise FloatingPointError("Nonfinite held-out language NLL")
        sums = torch.zeros(len(items), dtype=torch.float64).scatter_add_(
            0, active.nonzero()[:, 0].cpu(), losses.double().cpu()
        )
        counts = active.sum(1).cpu()
        for i, (source, _) in enumerate(items):
            by_source[source]["nll_sum_nats"] += float(sums[i])
            by_source[source]["targets"] += int(counts[i])
            by_source[source]["windows"] += 1

    for example in examples:
        pending.append(example)
        windows += 1
        if len(pending) == batch_size:
            consume(pending)
            pending = []
    if pending:
        consume(pending)
    rows = [
        {"source_id": source, **values} for source, values in sorted(by_source.items())
    ]
    if not rows:
        raise ValueError("No held-out general sources")
    nll = sum(r["nll_sum_nats"] for r in rows)
    targets = sum(r["targets"] for r in rows)
    mean = nll / targets
    return {
        "nll_nats_per_target": mean,
        "perplexity": math.exp(min(mean, 80)),
        "perplexity_clipped": mean > 80,
        "targets": targets,
        "windows": windows,
        "sources": len(rows),
        "per_source": rows,
        "uncertainty": source_interval(rows, draws=draws),
    }


def general_perplexity(
    plan_path,
    checkpoint,
    *,
    phase="post",
    split="validation",
    selection=None,
    general_corpus=None,
    device="cpu",
    draws=2000,
):
    if type(draws) is not int or draws < 100:
        raise ValueError("At least100 whole-source bootstrap draws required")
    if device != "cpu":
        raise ValueError("Reviewed language evaluation uses CPU/FP64")
    if split not in {"validation", "test"} or phase not in {"foundation", "post"}:
        raise ValueError("Declared phase and held-out split required")
    if phase == "foundation" and split != "validation":
        raise ValueError("Foundation feasibility cannot release general test text")
    digest = sha256(checkpoint)
    if phase == "foundation":
        plan = load_foundation_plan(plan_path)
        foundation = plan
        saved = torch.load(checkpoint, map_location="cpu", weights_only=True)
        run = next(
            (r for r in plan["runs"] if r == saved.get("identity", {}).get("run")), None
        )
        if run is None:
            raise ValueError("Unknown foundation run")
        check_complete_parent(saved, plan, run)
        frozen = None
    else:
        plan = load_plan(plan_path)
        frozen = read_selection(plan, selection) if split == "test" else None
        saved = complete_checkpoint(checkpoint, plan)
        run = saved["run"]
        if frozen and (
            run["arm"] not in frozen["analysis_registration"]["test_arms"]
            or digest != frozen["checkpoints"][run["id"]]["sha256"]
        ):
            raise ValueError("General test checkpoint not frozen for this run")
        foundation = load_foundation_plan(
            plan["parents"][run["parent_key"]]["foundation_plan"]
        )
    if split == "test":
        if (
            frozen["analysis_registration"].get("general_text_test_policy")
            != GENERAL_TEST_POLICY
        ):
            raise ValueError(
                "General-text test policy must be registered before test release"
            )
        if (
            general_corpus is None
            or sha256(general_corpus) != foundation["corpus_sha256"]
        ):
            raise ValueError("Exact frozen general corpus snapshot required")
    if (
        saved.get("config") != plan["models"][run["kind"]]["config"]
        or saved.get("tokenizer_spec") != foundation["tokenizer_spec"]
        or any(
            t.is_floating_point() and t.dtype != torch.float32
            for t in saved["model"].values()
        )
    ):
        raise ValueError("Model/tokenizer/FP32 declaration differs")
    previous = (
        torch.backends.mha.get_fastpath_enabled(),
        torch.backends.cuda.matmul.allow_tf32,
        torch.backends.cudnn.allow_tf32,
    )
    try:
        torch.backends.mha.set_fastpath_enabled(False)
        if device.startswith("cuda"):
            torch.backends.cuda.matmul.allow_tf32 = False
            torch.backends.cudnn.allow_tf32 = False
        cfg = FoundationConfig(**plan["models"][run["kind"]]["config"])
        model = build_foundation(cfg, seed=run["seed"]).double().cpu()
        model.load_state_dict(saved["model"], strict=True)
        del saved
        learned = weights_sha256(model)
        tokenizer = FrozenTokenizer(
            foundation["tokenizer"], foundation["tokenizer_spec"]
        )
        if split == "validation":
            data = TokenDataset(foundation["data_dir"], "validation", "lm")
            sources = read_rows(
                Path(foundation["data_dir"]) / "validation-lm.sources.jsonl"
            )
            if len(sources) != len(data):
                raise ValueError("Encoded source/window index mismatch")
            examples = ((sources[i]["source_id"], data[i]) for i in range(len(data)))
        else:
            examples = heldout_test_examples(general_corpus, tokenizer, cfg.context)
        started = time.perf_counter()
        result = summarize_language(
            model,
            examples,
            pad_id=tokenizer.pad_id,
            context=cfg.context,
            batch_size=plan["config"]["batch_size"],
            device=device,
            draws=draws,
        )
        elapsed = time.perf_counter() - started
        if weights_sha256(model) != learned or sha256(checkpoint) != digest:
            raise ValueError("Weights/checkpoint changed during language evaluation")
        return {
            **result,
            "phase": phase,
            "split": split,
            "kind": "general_text_next_token_perplexity",
            "plan_id": plan["plan_id"],
            "run": run,
            "checkpoint_sha256": digest,
            "actual_parameters": sum(p.numel() for p in model.parameters()),
            "tokenizer_sha256": foundation["tokenizer_spec"]["sha256"],
            "general_corpus_sha256": foundation["corpus_sha256"],
            "encoded_manifest_sha256": foundation["data_manifest_sha256"]
            if split == "validation"
            else None,
            "selection_sha256": sha256(selection) if frozen else None,
            "implementation_sha256": source_sha256(__file__),
            "torch": str(torch.__version__),
            "device": device,
            "gpu": torch.cuda.get_device_name() if device.startswith("cuda") else None,
            "mha_fastpath_enabled": False,
            "inference_precision": "float64",
            "inference_backend": BACKEND,
            "optimizer_updates": 0,
            "weights_and_checkpoint_unchanged": True,
            "temperature_or_topk_applied": False,
            "EOS_supervised": True,
            "state_reset_each_window": True,
            "evaluation_seconds": elapsed,
            "writing_or_logic_measured": False,
            "metric_unit": "natural-log NLL per frozen BPE target, including EOS; not directly comparable across tokenizers",
        }
    finally:
        torch.backends.mha.set_fastpath_enabled(previous[0])
        torch.backends.cuda.matmul.allow_tf32 = previous[1]
        torch.backends.cudnn.allow_tf32 = previous[2]
