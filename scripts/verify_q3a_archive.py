"""Verify a downloaded Q3-A evidence ZIP without extracting or loading pickle.

Checks hashes, run identities and contiguous finite metric/target accounting.
An externally recorded archive digest is required; matching hashes alone do not
establish scientific validity, human evaluation, or cloud persistence.
"""

import argparse
import hashlib
import json
import math
import re
import stat
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath


def digest_file(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_archive(path, expected_digest, plan_id):
    path = Path(path)
    actual = digest_file(path)
    if not re.fullmatch("[a-f0-9]{64}", expected_digest) or actual != expected_digest:
        raise ValueError("Archive digest does not match external receipt")
    runs = {}
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = [x.filename for x in entries]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP member")
        if sum(x.file_size for x in entries) > 2_000_000_000:
            raise ValueError("Evidence archive exceeds size bound")
        for member in entries:
            name = PurePosixPath(member.filename)
            if (
                name.is_absolute()
                or ".." in name.parts
                or "\\" in member.filename
                or ":" in member.filename
                or stat.S_ISLNK(member.external_attr >> 16)
                or member.file_size > 500_000_000
            ):
                raise ValueError("Unsafe or oversized archive member")
        manifest = json.loads(archive.read("SHA256SUMS.json"))
        files = {x.filename for x in entries if not x.is_dir()}
        if files - {"SHA256SUMS.json"} != set(manifest):
            raise ValueError("Manifest does not cover exactly the archive files")
        for name, expected in manifest.items():
            with archive.open(name) as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest != expected:
                raise ValueError(f"Member hash mismatch: {name}")
        for kind in ("mingru", "transformer"):
            run_id = f"warmup-{kind}-s0"
            prefix = "runs/" + run_id + "/"
            record = json.loads(archive.read(prefix + "run.json"))
            run = record["run"]
            stats = record["stats"]
            if (
                record["plan_id"] != plan_id
                or run["id"] != run_id
                or run["kind"] != kind
                or run["phase"] != "warmup"
                or run["seed"] != 0
                or not 0 < stats["trained_targets"] <= run["targets"]
                or record["complete"] != (stats["trained_targets"] == run["targets"])
            ):
                raise ValueError(f"Run identity/budget mismatch: {run_id}")
            targets, count = 0, 0
            with archive.open(prefix + "metrics.jsonl") as stream:
                for count, line in enumerate(stream, 1):
                    row = json.loads(line)
                    delta = row["target_delta"]
                    if type(delta) is not int or delta <= 0 or row["update"] != count:
                        raise ValueError(
                            f"Noncontiguous metric or invalid delta: {run_id}"
                        )
                    targets += delta
                    if row["targets"] != targets:
                        raise ValueError(f"Metric target sum mismatch: {run_id}")
                    for key in ("ce", "objective", "gradient_norm", "seconds"):
                        if not math.isfinite(row[key]):
                            raise ValueError(f"Nonfinite {key}: {run_id}")
                    if row["seconds"] < 0 or row["gradient_norm"] < 0:
                        raise ValueError(f"Invalid timing/gradient norm: {run_id}")
            if count != stats["updates"] or targets != stats["trained_targets"]:
                raise ValueError(f"Metric totals differ from run receipt: {run_id}")
            checkpoint = prefix + ("final.pt" if record["complete"] else "latest.pt")
            if checkpoint not in manifest:
                raise ValueError(f"Missing checkpoint: {run_id}")
            # Complete final.pt and latest.pt have different serialized metadata.
            if (
                not record["complete"]
                and manifest[checkpoint] != record["checkpoint_sha256"]
            ):
                raise ValueError(f"Partial checkpoint differs from receipt: {run_id}")
            runs[run_id] = {
                "complete": record["complete"],
                "actual_parameters": record["actual_parameters"],
                "stats": stats,
                "checkpoint_file": checkpoint,
                "checkpoint_sha256": manifest[checkpoint],
                "metric_rows_verified": count,
            }
    return {
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "archive_sha256": actual,
        "archive_bytes": path.stat().st_size,
        "plan_id": plan_id,
        "members_verified": len(manifest),
        "runs": runs,
        "verifier_source_sha256": digest_file(__file__),
        "optimizer_updates_in_verification": 0,
        "checkpoint_pickle_loaded": False,
        "scope": "byte integrity and log accounting, not scientific validity or cloud provenance",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--plan-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if Path(args.output).exists():
        raise FileExistsError(args.output)
    report = verify_archive(args.archive, args.sha256, args.plan_id)
    with Path(args.output).open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
