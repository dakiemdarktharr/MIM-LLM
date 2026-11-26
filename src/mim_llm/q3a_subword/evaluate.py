"""Natural subword continuations and a complete-panel test-release contract.

No test output or human score is produced by preparation. Model input contains
only the prompt; oracle state is retained solely in the private scoring record.
"""

import json
import math
from pathlib import Path

import torch

from ..foundation.codec import FrozenTokenizer
from ..foundation.modeling import FoundationConfig, build_foundation
from ..q3a import data
from ..q3a.io import read_json, read_rows, sha256, signature, source_sha256, write_json
from .inference import BACKEND, generate
from .plan import load_plan

ROLES = ("base", "effective", "noop")


def complete_checkpoint(path, plan):
    saved = torch.load(path, map_location="cpu", weights_only=True)
    run = next((r for r in plan["runs"] if r == saved.get("run")), None)
    if run is None:
        raise ValueError("Unknown subword post run")
    parent = plan["parents"][run["parent_key"]]["checkpoint_sha256"]
    identity, stats = saved.get("identity", {}), saved.get("stats", {})
    if (
        saved.get("plan_id") != plan["plan_id"]
        or identity.get("plan_id") != plan["plan_id"]
        or identity.get("run") != run
        or identity.get("parent_sha256") != parent
        or saved.get("parent_sha256") != parent
        or identity.get("precision") != "float32_TF32_disabled"
        or identity.get("mha_fastpath_enabled") is not False
        or saved.get("complete") is not True
        or type(stats.get("targets")) is not int
        or stats["targets"] != run["targets"]
        or type(stats.get("updates")) is not int
        or stats["updates"] < 1
        or saved.get("config") != plan["models"][run["kind"]]["config"]
        or saved.get("tokenizer_spec") != plan["tokenizer_spec"]
    ):
        raise ValueError("Require the complete declared subword post checkpoint")
    if any(
        v.is_floating_point() and v.dtype != torch.float32
        for v in saved["model"].values()
    ):
        raise ValueError("Checkpoint is not the declared FP32 model")
    return saved


def validate_registration(plan, registration):
    from . import analysis
    from .language_eval import GENERAL_TEST_POLICY

    effect, cap = (
        registration.get("smallest_useful_effect"),
        registration.get("gpu_hours_cap_per_study"),
    )
    if (
        registration.get("status") != "frozen_before_test_generation"
        or registration.get("plan_id") != plan["plan_id"]
        or registration.get("test_results_used") is not False
        or registration.get("primary_contrast") != ["A1", "A2"]
        or registration.get("primary_metric") != analysis.PRIMARY_METRIC
        or registration.get("analysis_version") != analysis.VERSION
        or registration.get("analysis_source_sha256")
        != source_sha256(analysis.__file__)
        or registration.get("quality_aggregation") != analysis.QUALITY_RULE
        or registration.get("complete_source_seed_grid_required") is not True
        or registration.get("two_independent_readers_planned") is not True
        or registration.get("general_text_test_policy") != GENERAL_TEST_POLICY
        or registration.get("inference_backend") != BACKEND
        or not registration.get("sample_method_and_rationale", "").strip()
        or type(effect) not in (int, float)
        or not math.isfinite(effect)
        or not 0 < effect < 1
        or type(cap) not in (int, float)
        or not math.isfinite(cap)
        or cap <= 0
        or cap != plan["config"]["gpu_hours_cap_per_study"]
    ):
        raise ValueError("Freeze a complete, measured subword analysis registration")
    arms = registration.get("test_arms", [])
    if len(set(arms)) != len(arms) or not {"A1", "A2"} <= set(arms) <= set(
        plan["config"]["arms"]
    ):
        raise ValueError("Register included test arms with the primary A1/A2 contrast")
    sources = registration.get("test_source_ids", [])
    if not sources or len(set(sources)) != len(sources):
        raise ValueError("Predeclare unique complete-source test IDs")


def freeze_selection(
    plan_path,
    checkpoint_paths,
    registration_path,
    output,
    *,
    rationale,
    validation_evidence,
):
    if Path(output).exists():
        raise FileExistsError(output)
    plan = load_plan(plan_path)
    if plan["writing_gate"] is None or not rationale.strip() or not validation_evidence:
        raise ValueError("Reviewed writing and validation evidence required")
    registration = read_json(registration_path)
    validate_registration(plan, registration)
    checkpoints = {}
    for path in checkpoint_paths:
        saved = complete_checkpoint(path, plan)
        run = saved["run"]
        if run["id"] in checkpoints:
            raise ValueError("Duplicate selected run")
        checkpoints[run["id"]] = {
            "path": str(path),
            "sha256": sha256(path),
            "parent_sha256": saved["parent_sha256"],
        }
    if set(checkpoints) != {r["id"] for r in plan["runs"]} or len(checkpoints) != 24:
        raise ValueError("Complete all 24 declared post runs before test release")
    evidence = [{"path": str(p), "sha256": sha256(p)} for p in validation_evidence]
    # No model/performance is evaluated here. Test source membership is checked
    # only AFTER the fixed configuration, registration and all weights exist.
    available = {
        r["source_id"] for r in read_rows(Path(plan["data_dir"]) / "test.jsonl")
    }
    if not set(registration["test_source_ids"]) <= available:
        raise ValueError("Registered source ID outside the locked test split")
    value = {
        "schema_version": 1,
        "plan_id": plan["plan_id"],
        "dataset_id": plan["dataset_id"],
        "test_sha256": plan["data_sha256"]["test.jsonl"],
        "decoding": plan["config"]["decoding"],
        "checkpoints": checkpoints,
        "selection_frozen": True,
        "test_results_used": False,
        "analysis_registration": registration,
        "analysis_registration_path": str(registration_path),
        "analysis_registration_sha256": sha256(registration_path),
        "validation_rationale": rationale,
        "validation_evidence": evidence,
        "writing_gate": plan["writing_gate"],
        "test_performance_measured": False,
    }
    value["selection_id"] = signature(value)
    write_json(output, value)
    return value


def read_selection(plan, path):
    if path is None:
        raise ValueError("Test is locked until the complete selection is frozen")
    value = read_json(path)
    if signature({k: v for k, v in value.items() if k != "selection_id"}) != value.get(
        "selection_id"
    ):
        raise ValueError("Changed frozen selection")
    if (
        value.get("selection_frozen") is not True
        or value.get("test_results_used") is not False
        or value["plan_id"] != plan["plan_id"]
        or value["dataset_id"] != plan["dataset_id"]
        or value["test_sha256"] != plan["data_sha256"]["test.jsonl"]
        or value["decoding"] != plan["config"]["decoding"]
        or value["writing_gate"] != plan["writing_gate"]
        or len(value["checkpoints"]) != 24
        or set(value["checkpoints"]) != {r["id"] for r in plan["runs"]}
    ):
        raise ValueError("Selection does not match the complete subword plan")
    validate_registration(plan, value["analysis_registration"])
    if (
        sha256(value["analysis_registration_path"])
        != value["analysis_registration_sha256"]
        or read_json(value["analysis_registration_path"])
        != value["analysis_registration"]
    ):
        raise ValueError("Analysis registration changed after selection")
    for evidence in value["validation_evidence"]:
        if sha256(evidence["path"]) != evidence["sha256"]:
            raise ValueError("Validation evidence changed after selection")
    return value


def generate_panel(
    plan_path, checkpoint, output, *, split="validation", device="cpu", selection=None
):
    if device != "cpu":
        raise ValueError("Reviewed generation uses the canonical CPU/FP64 backend")
    previous_mha = torch.backends.mha.get_fastpath_enabled()
    previous_matmul = torch.backends.cuda.matmul.allow_tf32
    previous_cudnn = torch.backends.cudnn.allow_tf32
    try:
        torch.backends.mha.set_fastpath_enabled(False)
        if device.startswith("cuda"):
            torch.backends.cuda.matmul.allow_tf32 = False
            torch.backends.cudnn.allow_tf32 = False
        return _generate_panel(
            plan_path,
            checkpoint,
            output,
            split=split,
            device=device,
            selection=selection,
        )
    finally:
        torch.backends.mha.set_fastpath_enabled(previous_mha)
        torch.backends.cuda.matmul.allow_tf32 = previous_matmul
        torch.backends.cudnn.allow_tf32 = previous_cudnn


def _generate_panel(
    plan_path, checkpoint, output, *, split="validation", device="cpu", selection=None
):
    if split not in {"validation", "test"}:
        raise ValueError("Held-out validation/test panels only")
    plan = load_plan(plan_path)
    frozen = read_selection(plan, selection) if split == "test" else None
    saved = complete_checkpoint(checkpoint, plan)
    run, digest = saved["run"], sha256(checkpoint)
    if frozen and run["arm"] not in frozen["analysis_registration"]["test_arms"]:
        raise ValueError("Run is outside the registered test-arm sample")
    if frozen and frozen["checkpoints"][run["id"]]["sha256"] != digest:
        raise ValueError("Checkpoint not in the frozen selection for this run")
    output = Path(output)
    started_path, receipt_path = (
        Path(str(output) + ".started.json"),
        Path(str(output) + ".receipt.json"),
    )
    if any(p.exists() for p in (output, started_path, receipt_path)):
        raise FileExistsError(output)
    model = (
        build_foundation(FoundationConfig(**saved["config"]), seed=run["seed"])
        .double()
        .cpu()
    )
    model.load_state_dict(saved["model"], strict=True)
    model.eval()
    del saved
    actual_parameters = sum(p.numel() for p in model.parameters())
    if actual_parameters != plan["models"][run["kind"]]["actual_parameters"]:
        raise ValueError("Parameter count differs from the frozen model")
    tokenizer = FrozenTokenizer(plan["tokenizer"], plan["tokenizer_spec"])
    decoding = plan["config"]["decoding"]
    sources = (
        set(frozen["analysis_registration"]["test_source_ids"]) if frozen else None
    )
    bundles = read_rows(Path(plan["data_dir"]) / (split + ".jsonl"))
    bundles = [b for b in bundles if sources is None or b["source_id"] in sources]
    if (
        not bundles
        or len({b["source_id"] for b in bundles}) != len(bundles)
        or (sources is not None and {b["source_id"] for b in bundles} != sources)
    ):
        raise ValueError("Incomplete requested source panel")
    identity = {
        "plan_id": plan["plan_id"],
        "run": run,
        "checkpoint_sha256": digest,
        "split": split,
        "selection_sha256": sha256(selection) if frozen else None,
        "actual_parameters": actual_parameters,
        "tokenizer_sha256": plan["tokenizer_spec"]["sha256"],
        "decoding": decoding,
        "optimizer_updates": 0,
        "human_labels": False,
        "inference_gold_state_table": False,
        "mha_fastpath_enabled": False,
        "inference_backend": BACKEND,
        "inference_precision": "float64",
        "torch": str(torch.__version__),
        "device": device,
        "gpu": torch.cuda.get_device_name() if device.startswith("cuda") else None,
        "expected_samples": len(bundles) * len(ROLES) * len(decoding["seeds"]),
    }
    write_json(started_path, identity)
    count = 0
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        for bundle in bundles:
            data.validate_bundle(bundle)
            for role in ROLES:
                scenario = bundle["scenarios"][role]
                for seed in decoding["seeds"]:
                    sample = generate(
                        model,
                        tokenizer,
                        scenario["prompt"],
                        max_new_tokens=decoding["max_new_tokens"],
                        temperature=decoding["temperature"],
                        top_k=decoding["top_k"],
                        seed=seed,
                        device=device,
                    )
                    row = {
                        **sample,
                        "source_id": bundle["source_id"],
                        "scenario_id": scenario["id"],
                        "role": role,
                        "split": split,
                        "world": scenario["world"],
                        "expected_facts": scenario["facts"],
                        "mandatory": scenario["mandatory"],
                        "pairs": bundle["pairs"],
                        "depth": bundle["depth"],
                        "run": run,
                        "plan_id": plan["plan_id"],
                        "checkpoint_sha256": digest,
                        "decode_seed": seed,
                        "tokenizer_sha256": plan["tokenizer_spec"]["sha256"],
                        "actual_parameters": actual_parameters,
                        "primary_evaluation": split == "test",
                        "inference_gold_state_table": False,
                        "inference_backend": BACKEND,
                    }
                    row["generation_id"] = signature(
                        {
                            k: row[k]
                            for k in (
                                "scenario_id",
                                "run",
                                "checkpoint_sha256",
                                "decode_seed",
                            )
                        }
                    )
                    handle.write(
                        json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n"
                    )
                    handle.flush()
                    count += 1
    if sha256(checkpoint) != digest or count != identity["expected_samples"]:
        raise ValueError(
            "Checkpoint or panel changed during generation; retain partial evidence"
        )
    result = {
        **identity,
        "complete": True,
        "generations": count,
        "output_sha256": sha256(output),
        "primary_oracle_scores_computed": False,
    }
    write_json(receipt_path, result)
    return result


def prepare_blind_packet(plan_path, generation_files, output, *, selection=None):
    """Validate costly annotation inputs before producing any blank label file."""
    from ..q3a.evaluate import blind_packet
    from ..q3a_reviewed_analysis import validate_panel
    from .analysis import join_generations, verify_sources

    plan = load_plan(plan_path)
    rows = [r for path in generation_files for r in read_rows(path)]
    if not rows or len({r["split"] for r in rows}) != 1:
        raise ValueError("One nonempty held-out split required")
    split = rows[0]["split"]
    if split not in {"validation", "test"}:
        raise ValueError("Held-out panels only")
    frozen = read_selection(plan, selection) if split == "test" else None
    key = [{"item_id": f"validation-only-{i}", **r} for i, r in enumerate(rows)]
    # The temporary key never leaves this function. The real packet is freshly
    # shuffled with architecture IDs kept solely in its separate private key.
    join_generations(plan, key, generation_files)
    verify_sources(plan, rows, split, frozen=frozen)
    panel = validate_panel(
        key,
        seeds=plan["config"]["seeds"] if frozen else None,
        backbones=plan["config"]["backbones"] if frozen else None,
        arms=frozen["analysis_registration"]["test_arms"] if frozen else None,
        decodes=plan["config"]["decoding"]["seeds"],
        sources=frozen["analysis_registration"]["test_source_ids"] if frozen else None,
    )
    result = blind_packet(generation_files, output)
    return {**result, "complete_panel": panel, "actual_human_labels": 0}
