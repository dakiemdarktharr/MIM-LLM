"""Plan parameter-matched runs; execute only with an explicit --run flag."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from .models import ModelConfig, build_model, parameter_count
from .protocol import match_width
from .tokenizer import load_tokenizer
from .train import file_sha256, train


def run_matrix(
    corpus: str,
    output_dir: str,
    *,
    tokenizer_model: str | None = None,
    reference_width: int = 192,
    layers: int = 2,
    context: int = 256,
    kinds: list[str] | None = None,
    seeds: list[int] | None = None,
    max_train_tokens: int = 100_000,
    batch_size: int = 8,
    learning_rate: float = 3e-4,
    device: str = "auto",
    run: bool = False,
) -> dict[str, Any]:
    kinds = kinds or ["mim", "mim_pair"]
    seeds = seeds or [0, 1, 2]
    if len(kinds) != len(set(kinds)) or len(seeds) != len(set(seeds)):
        raise ValueError("Duplicate model kind or seed")
    vocab = load_tokenizer(tokenizer_model).vocab_size
    reference = ModelConfig(
        kind="mim",
        width=reference_width,
        layers=layers,
        context=context,
        vocab_size=vocab,
    )
    target = parameter_count(build_model(reference))
    matched = []
    for kind in kinds:
        template = replace(reference, kind=kind)
        result = match_width(target, template)
        if abs(result["relative_parameter_gap"]) > 0.05:
            raise ValueError(f"Could not match {kind} within 5% parameters")
        matched.append(result)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    plan = {
        "corpus": str(Path(corpus).resolve()),
        "corpus_sha256": file_sha256(corpus),
        "tokenizer_model": str(Path(tokenizer_model).resolve())
        if tokenizer_model
        else None,
        "tokenizer_sha256": file_sha256(tokenizer_model) if tokenizer_model else None,
        "reference_parameters": target,
        "models": matched,
        "seeds": seeds,
        "max_train_tokens_per_run": max_train_tokens,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "device": device,
        "training_executed": False,
    }
    plan_path = output / "matrix-plan.json"
    if plan_path.exists():
        old = json.loads(plan_path.read_text(encoding="utf-8"))
        if {
            key: value
            for key, value in old.items()
            if key not in {"training_executed", "completed_runs"}
        } != {
            key: value
            for key, value in plan.items()
            if key not in {"training_executed", "completed_runs"}
        }:
            raise FileExistsError("Existing matrix plan differs")
        plan["completed_runs"] = old.get("completed_runs", [])
        plan["training_executed"] = old.get("training_executed", False)
        for run_name in plan["completed_runs"]:
            manifest_path = output / run_name / "manifest.json"
            if not manifest_path.exists():
                raise FileNotFoundError(f"Completed run has no manifest: {run_name}")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest["corpus_sha256"] != plan["corpus_sha256"]:
                raise ValueError(f"Completed run corpus hash differs: {run_name}")
            if manifest["tokenizer_sha256"] != plan["tokenizer_sha256"]:
                raise ValueError(f"Completed run tokenizer hash differs: {run_name}")
            if not (output / run_name / "best.pt").exists():
                raise FileNotFoundError(
                    f"Completed run has no best checkpoint: {run_name}"
                )
    else:
        plan["completed_runs"] = []
    plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    if run:
        for model in matched:
            config = ModelConfig(**model["config"])
            for seed in seeds:
                run_name = f"{config.kind}-seed{seed}"
                if run_name in plan["completed_runs"]:
                    continue
                run_dir = output / run_name
                if (run_dir / "manifest.json").exists():
                    raise FileExistsError(
                        f"Completed run missing from plan; inspect before proceeding: {run_dir}"
                    )
                train(
                    corpus,
                    run_dir,
                    config,
                    seed=seed,
                    batch_size=batch_size,
                    learning_rate=learning_rate,
                    max_train_tokens=max_train_tokens,
                    device=device,
                    tokenizer_model=tokenizer_model,
                    resume=(run_dir / "latest.pt").exists(),
                )
                plan["completed_runs"].append(run_name)
                plan_path.write_text(
                    json.dumps(plan, indent=2) + "\n", encoding="utf-8"
                )
        plan["training_executed"] = True
        plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    return plan
