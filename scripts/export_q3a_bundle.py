"""Create a LOCAL preparation bundle for Colab; does not execute training."""

import argparse
import json
import zipfile
from pathlib import Path

from mim_llm.q3a.io import sha256
from mim_llm.q3a.plan import load_plan


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    root = Path.cwd().resolve()
    plan = load_plan(a.plan)
    output = Path(a.output)
    if output.exists():
        raise FileExistsError(output)
    files = [
        root / "pyproject.toml",
        root / "README.md",
        root / "configs/training_permission.json",
        root / "configs/q3a/pilot.json",
        root / a.plan,
        root / plan["warmup"],
        root / (plan["warmup"] + ".manifest.json"),
    ]
    files += list((root / "src/mim_llm").rglob("*.py")) + list(
        (root / plan["data_dir"]).glob("*.json*")
    )
    files += [root/'docs/Q3_A_PRETRAIN_RUNBOOK.vi.md']
    files += list((root / "configs/q3a").glob("*.json"))
    files += [root / "docs/Q3_A_ANNOTATION_GUIDE.md"]
    unique = sorted(set(files))
    for f in unique:
        if not f.resolve().is_relative_to(root) or not f.is_file():
            raise ValueError("Bundle source outside workspace or missing")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for f in unique:
            archive.write(f, f.relative_to(root).as_posix())
        archive.writestr(
            "BUNDLE-MANIFEST.json",
            json.dumps(
                {
                    "plan_id": plan["plan_id"],
                    "files": {
                        f.relative_to(root).as_posix(): sha256(f) for f in unique
                    },
                    "training_authorized": False,
                    "tinystories_license": "cdla-sharing-1.0",
                    "source": "https://huggingface.co/datasets/roneneldan/TinyStories",
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
                "training_started": False,
            }
        )
    )


if __name__ == "__main__":
    main()
