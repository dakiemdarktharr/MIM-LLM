"""Private source/token-array bundle; no test tokens, weights or credentials."""

import argparse
import json
import zipfile
from pathlib import Path

from mim_llm.foundation.plan import load_plan
from mim_llm.q3a.io import read_json, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    plan = load_plan(args.plan)
    permission = read_json("configs/training_permission.json")
    if plan["plan_id"] not in permission["authorized_plan_ids"]:
        raise ValueError("Exact new plan not recorded")
    files = [
        root / p
        for p in (
            "pyproject.toml",
            "README.md",
            "DATA_NOTICES.md",
            "configs/training_permission.json",
            "docs/Q3_A_FOUNDATION_PROTOCOL_20261126.vi.md",
            "scripts/run_q3a_colab.py",
            "scripts/run_q3a_foundation.py",
            args.plan,
            plan["tokenizer"],
        )
    ]
    files += list((root / "src/mim_llm").rglob("*.py"))
    files += [
        root / plan["data_dir"] / n
        for n in read_json(Path(plan["data_dir"]) / "manifest.json")["files"]
    ]
    files += [
        root / plan["data_dir"] / "manifest.json",
        root / "data/raw/q3a-foundation-20261126.jsonl.manifest.json",
    ]
    files = sorted(set(files))
    for file in files:
        if not file.is_file() or not file.resolve().is_relative_to(root):
            raise ValueError("Missing/unsafe bundle member")
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in files:
            archive.write(file, file.relative_to(root).as_posix())
        archive.writestr(
            "BUNDLE-MANIFEST.json",
            json.dumps(
                {
                    "plan_id": plan["plan_id"],
                    "files": {f.relative_to(root).as_posix(): sha256(f) for f in files},
                    "test_tokenized": False,
                    "external_weights_included": False,
                },
                indent=2,
            ),
        )
    print(
        json.dumps(
            {
                "file": str(out),
                "bytes": out.stat().st_size,
                "sha256": sha256(out),
                "plan_id": plan["plan_id"],
            }
        )
    )


if __name__ == "__main__":
    main()
