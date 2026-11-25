"""Local portable bundle; never includes weights, labels, PDFs or paid jobs."""

import argparse
import json
import zipfile
from pathlib import Path

from mim_llm.q3a.io import read_json, sha256
from mim_llm.q3a.plan import load_plan as load_a
from mim_llm.q3bc.plan import load_plan


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--registry", default="artifacts/three-q3-final-20261126/registry.json"
    )
    p.add_argument("--output", default="artifacts/three-q3-pretrain.zip")
    a = p.parse_args()
    root = Path.cwd().resolve()
    registry = read_json(a.registry)
    files = [
        root / a.registry,
        root / "pyproject.toml",
        root / "README.md",
        root / "DATA_NOTICES.md",
        root / "configs/training_permission.json",
    ]
    for study, plan_path in registry["plans"].items():
        plan = load_a(plan_path) if study == "a" else load_plan(plan_path)
        files.append(root / plan_path)
        files.extend((root / plan["data_dir"]).glob("*.json*"))
        files.extend((root / f"configs/q3{study}").glob("*.json"))
        if study == "a":
            files += [root / plan["warmup"], root / (plan["warmup"] + ".manifest.json")]
            warmup_manifest = read_json(root / (plan["warmup"] + ".manifest.json"))
            if warmup_manifest.get("original_corpus"):
                files += [
                    root / warmup_manifest["original_corpus"],
                    root / (warmup_manifest["original_corpus"] + ".manifest.json"),
                ]
    files += list((root / "src/mim_llm").rglob("*.py"))
    files += [p for p in (root / "docs").glob("*") if p.suffix in {".md", ".json"}]
    files += list((root / "scripts").glob("*.py"))
    files += list((root / "tests").glob("*.py"))
    files += list((root / "notebooks").glob("*.ipynb"))
    files += [
        p for p in (root / "papers").rglob("*") if p.suffix in {".tex", ".json", ".md"}
    ]
    files = sorted(set(files))
    output = Path(a.output)
    if output.exists():
        raise FileExistsError(output)
    for f in files:
        if not f.resolve().is_relative_to(root) or not f.is_file():
            raise ValueError("Missing bundle member or source outside workspace")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f.relative_to(root).as_posix())
        z.writestr(
            "BUNDLE-MANIFEST.json",
            json.dumps(
                {
                    "registry": a.registry,
                    "files": {f.relative_to(root).as_posix(): sha256(f) for f in files},
                    "training_authorized": False,
                    "C_production_bank_exists": False,
                    "external_dataset_license": "TinyStories CDLA-Sharing-1.0; retain original provenance/terms",
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
