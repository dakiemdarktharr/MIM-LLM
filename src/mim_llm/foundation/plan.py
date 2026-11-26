"""Content addressed, bounded language-foundation feasibility plans."""

from dataclasses import asdict
from pathlib import Path

from ..q3a.io import read_json, sha256, signature, source_sha256, write_json
from .modeling import FoundationConfig, build_foundation, parameter_breakdown


def fingerprints():
    root = Path(__file__).resolve().parents[1]
    files = list((root / "foundation").glob("*.py")) + [
        root / "models.py",
        root / "training_gate.py",
        root / "q3a/io.py",
    ]
    return {p.relative_to(root).as_posix(): source_sha256(p) for p in sorted(files)}


def validate_data(root, expected=None):
    root = Path(root)
    if expected is not None and sha256(root / "manifest.json") != expected:
        raise ValueError("Changed encoded manifest")
    manifest = read_json(root / "manifest.json")
    if not manifest.get("complete") or manifest["test_tokenized"]:
        raise ValueError("Incomplete preparation or test tokenized")
    for name, info in manifest["files"].items():
        if Path(name).name != name:
            raise ValueError("Unsafe corpus filename")
        path = root / name
        if path.stat().st_size != info["bytes"] or sha256(path) != info["sha256"]:
            raise ValueError("Changed encoded corpus file: " + name)
    return manifest


def make_plan(config, data_dir, tokenizer, output):
    manifest = validate_data(data_dir)
    if sha256(tokenizer) != manifest["tokenizer_spec"]["sha256"]:
        raise ValueError("Tokenizer/corpus mismatch")
    if config["context"] != manifest["context"]:
        raise ValueError("Context mismatch")
    if config["batch_size"] < 1 or config["grad_clip"] <= 0:
        raise ValueError("Invalid batch/clip")
    stages = config["stages"]
    if [s["name"] for s in stages] != ["lm", "sft"] or any(
        min(s["targets"], s["warmup_targets"], s["learning_rate"], s["minimum_lr"]) <= 0
        or s["minimum_lr"] > s["learning_rate"]
        or s["warmup_targets"] >= s["targets"]
        for s in stages
    ):
        raise ValueError("Invalid two-stage schedule")
    models = {}
    for kind, spec in config["models"].items():
        cfg = FoundationConfig(kind=kind, context=config["context"], **spec)
        model = build_foundation(cfg)
        models[kind] = {"config": asdict(cfg), **parameter_breakdown(model)}
    plan = {
        "schema_version": 1,
        "purpose": "one bounded replacement of failed language feasibility; not primary Q3-A",
        "config": config,
        "data_dir": Path(data_dir).as_posix(),
        "data_manifest_sha256": sha256(Path(data_dir) / "manifest.json"),
        "data_summary": manifest["splits"],
        "corpus_sha256": manifest["corpus_sha256"],
        "tokenizer": Path(tokenizer).as_posix(),
        "tokenizer_spec": manifest["tokenizer_spec"],
        "implementation_fingerprints": fingerprints(),
        "models": models,
        "runs": [{"id": f"foundation-{k}-s0", "kind": k, "seed": 0} for k in models],
        "test_locked": True,
        "measured_throughput": None,
    }
    plan["plan_id"] = signature(plan)
    write_json(output, plan)
    return plan


def load_plan(path, *, verify_inputs=True):
    plan = read_json(path)
    payload = {k: v for k, v in plan.items() if k != "plan_id"}
    if signature(payload) != plan["plan_id"]:
        raise ValueError("Changed plan")
    if plan["implementation_fingerprints"] != fingerprints():
        raise ValueError("Changed foundation implementation")
    if verify_inputs:
        manifest = validate_data(plan["data_dir"], plan["data_manifest_sha256"])
        if manifest["tokenizer_spec"] != plan["tokenizer_spec"]:
            raise ValueError("Changed tokenizer spec")
        if sha256(plan["tokenizer"]) != plan["tokenizer_spec"]["sha256"]:
            raise ValueError("Changed tokenizer")
    return plan
