"""Audit pinned candidate metadata only; never reads stories or trains a model."""

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

REVISION = "a24ddc17364666b7c13a425b9970c87368b03417"
BLOBS = {
    "story_meta.csv": "2e2f45b3512611e5c8fa35383f28d5d744aba89f",
    "LICENSE": "b6076b10d587404f9f73a523876eecc1deaa47e0",
    "README.md": "09fcb6ce539b670414fffc7a9fb1413102ba9a83",
}


def audit(directory):
    root = Path(directory)
    files = {}
    for name, expected in BLOBS.items():
        raw = (root / name).read_bytes()
        git_blob = hashlib.sha1(
            b"blob " + str(len(raw)).encode() + b"\0" + raw
        ).hexdigest()
        if git_blob != expected:
            raise ValueError("Metadata bytes differ from pinned Git blob: " + name)
        files[name] = {
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "git_blob": git_blob,
        }
    rows = list(
        csv.DictReader((root / "story_meta.csv").open(encoding="utf-8", newline=""))
    )
    tree_path = root / "tree-csv-inventory.json"
    tree = json.loads(tree_path.read_text(encoding="utf-8"))
    by_path = {entry["path"]: entry for entry in tree}
    if len(by_path) != len(tree):
        raise ValueError("Duplicate paths in inventory")
    folded = defaultdict(list)
    for entry in tree:
        folded[entry["path"].casefold()].append(entry)
    missing, case_only, different = [], [], []
    for row in rows:
        path = f"data-by-origin/section-stories/{row['origin']}/{row['filename']}-story.csv"
        found = by_path.get(path)
        if found is None:
            candidates = folded[path.casefold()]
            if len(candidates) == 1:
                found = candidates[0]
                case_only.append({"metadata_path": path, "actual_path": found["path"]})
            else:
                missing.append({"path": path, "casefold_candidates": len(candidates)})
        if found:
            # "all" is an intentional duplicate view, not an additional split.
            split_path = f"data-by-train-split/section-stories/{row['split']}/{row['filename']}-story.csv"
            others = folded[split_path.casefold()]
            if len(others) != 1 or others[0]["sha"] != found["sha"]:
                different.append(path)
    return {
        "as_of": "2026-11-27",
        "status": "source_metadata_audit_not_final_transfer_dataset",
        "repository": "https://github.com/uci-edu/FairytaleQAData",
        "revision": REVISION,
        "tree": "93b6c8fc9fa312cc15baf26edcc5c4f3fd6c19f1",
        "tree_inventory_sha256": hashlib.sha256(tree_path.read_bytes()).hexdigest(),
        "repository_license": "Apache-2.0",
        "license_scope": "repository; per-book edition/translator and source rights unresolved",
        "files": files,
        "metadata_stories": len(rows),
        "unique_story_origin_filename_ids": len(
            {(r["origin"], r["filename"]) for r in rows}
        ),
        "unique_filenames": len({r["filename"] for r in rows}),
        "upstream_splits": dict(Counter(r["split"] for r in rows)),
        "origin_book_groups": len({r["origin"] for r in rows}),
        "metadata_declared_counts": {
            key: sum(int(r[key]) for r in rows)
            for key in ("sections", "words", "questions")
        },
        "nonpositive_metadata_count_story_ids": {
            key: [r["filename"] for r in rows if int(r[key]) <= 0]
            for key in ("sections", "words", "questions")
        },
        "counts_are_metadata_not_independently_recounted_story_text": True,
        "tree_CSV_files": len(tree),
        "story_content_downloaded": False,
        "missing_section_story_paths": missing,
        "case_only_path_differences": case_only,
        "origin_vs_split_section_blob_differences_or_nonunique": different,
        "metadata_fields": list(rows[0]),
        "reviewed_transfer_pairs": 0,
        "actual_human_labels": 0,
        "training_use": False,
        "model_outputs_generated": False,
        "overlap_audit_completed": False,
        "context_audit_completed": False,
        "final_transfer_manifest": None,
        "implementation_sha256": hashlib.sha256(
            Path(__file__).read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", default="data/raw/fairytaleqa-a24ddc173646")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(output)
    result = audit(args.directory)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
