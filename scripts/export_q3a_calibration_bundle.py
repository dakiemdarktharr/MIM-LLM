"""Portable private calibration inputs; no weights, results, PDFs or credentials."""

import argparse
import json
import zipfile
from pathlib import Path

from mim_llm.q3a.io import read_json, sha256
from mim_llm.q3a.plan import load_plan


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    root = Path.cwd().resolve()
    plan = load_plan(a.plan)
    policy = read_json("configs/training_permission.json")
    if plan["plan_id"] not in policy["authorized_plan_ids"]:
        raise ValueError("Exact new plan must be recorded first")
    files = [
        root / name
        for name in (
            "pyproject.toml",
            "README.md",
            "DATA_NOTICES.md",
            "configs/training_permission.json",
            "configs/q3a/calibration2.json",
            "docs/SCOPE_REVIEW_BEFORE_TRAIN_20261126.vi.md",
            "docs/Q3_A_CALIBRATION2_PROTOCOL.vi.md",
            a.plan,
            "scripts/run_q3a_colab.py",
            "scripts/run_q3a_calibration.py",
            "scripts/inspect_q3a_warmup.py",
            "scripts/inspect_q3a_more_prefixes.py",
            "scripts/verify_q3a_trained_paths.py",
            "data/raw/q3a-tinystories.jsonl",
            "data/raw/q3a-tinystories.jsonl.manifest.json",
        )
    ]
    warmup = read_json(plan["warmup"] + ".manifest.json")
    for name in (plan["warmup"], warmup["original_corpus"]):
        files += [root / name, root / (name + ".manifest.json")]
    files += list((root / "src/mim_llm").rglob("*.py"))
    files += list((root / plan["data_dir"]).glob("*.json*"))
    files = sorted(set(files))
    for file in files:
        if not file.is_file() or not file.resolve().is_relative_to(root):
            raise ValueError("Missing or out-of-workspace member")
    output = Path(a.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in files:
            archive.write(file, file.relative_to(root).as_posix())
        archive.writestr(
            "BUNDLE-MANIFEST.json",
            json.dumps(
                {
                    "plan_id": plan["plan_id"],
                    "files": {
                        file.relative_to(root).as_posix(): sha256(file)
                        for file in files
                    },
                    "only_calibration_seed0_training": True,
                    "all_other_training_held": True,
                    "license": "TinyStories CDLA-Sharing-1.0; see DATA_NOTICES.md",
                },
                indent=2,
            ),
        )
    print(
        json.dumps(
            {
                "bundle": str(output),
                "bytes": output.stat().st_size,
                "sha256": sha256(output),
                "plan_id": plan["plan_id"],
                "training_started": False,
            }
        )
    )


if __name__ == "__main__":
    main()
