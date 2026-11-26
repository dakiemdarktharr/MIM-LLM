"""Hash and accounting verification of private foundation archives, no pickle."""

import argparse
import hashlib
import json
import math
import re
import stat
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from mim_llm.q3a.io import sha256, signature
from mim_llm.q3a_subword.resources import check_ledger_annex, resource_cap


def verify(path, expected_sha256, plan_id):
    if (
        not re.fullmatch("[a-f0-9]{64}", expected_sha256)
        or sha256(path) != expected_sha256
    ):
        raise ValueError("Archive differs from external digest")
    with zipfile.ZipFile(path) as archive:
        info = archive.infolist()
        names = [p.filename for p in info]
        if (
            len(names) != len(set(names))
            or sum(p.file_size for p in info) > 2_000_000_000
        ):
            raise ValueError("Duplicate/oversized ZIP")
        for p in info:
            name = PurePosixPath(p.filename)
            if (
                name.is_absolute()
                or ".." in name.parts
                or "\\" in p.filename
                or ":" in p.filename
                or stat.S_ISLNK(p.external_attr >> 16)
                or p.file_size > 500_000_000
            ):
                raise ValueError("Unsafe ZIP member")
        manifest = json.loads(archive.read("SHA256SUMS.json"))
        if set(manifest) != {p.filename for p in info if not p.is_dir()} - {
            "SHA256SUMS.json"
        }:
            raise ValueError("Incomplete hash manifest")
        for name, expected in manifest.items():
            with archive.open(name) as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != expected:
                    raise ValueError("Member digest mismatch")
        plans = [
            name
            for name in names
            if name.startswith("inputs/foundation_plan-") and name.endswith(".json")
        ]
        if len(plans) != 1:
            raise ValueError("Require one scientific plan")
        plan = json.loads(archive.read(plans[0]))
        if (
            plan["plan_id"] != plan_id
            or signature({k: v for k, v in plan.items() if k != "plan_id"}) != plan_id
        ):
            raise ValueError("Plan identity mismatch")
        ledger = json.loads(archive.read("foundation-budget.json"))
        annex = None
        if ledger.get("resource_annex"):
            candidates = [
                n
                for n in names
                if n.startswith("inputs/foundation_resource_annex-")
                and n.endswith(".json")
            ]
            if len(candidates) != 1:
                raise ValueError("Require one recorded resource annex")
            annex = json.loads(archive.read(candidates[0]))
            check_ledger_annex(ledger, annex, manifest[candidates[0]])
            for key in ("assessment", "profile"):
                member = "sessions/" + annex[key + "_filename"]
                if manifest.get(member) != annex[key + "_sha256"]:
                    raise ValueError("Resource annex evidence missing or changed")
        cap = resource_cap(plan, annex)
        if (
            ledger["plan_id"] != plan_id
            or len(ledger["invocations"]) > cap["maximum_invocations"]
        ):
            raise ValueError("Wrong ledger")
        events = []
        for name in sorted(
            n
            for n in names
            if n.startswith("sessions/") and n.endswith("-events.jsonl")
        ):
            events += [
                json.loads(line)
                for line in archive.read(name).splitlines()
                if line.strip()
            ]
        runs = {}
        for run in plan["runs"]:
            identifier = run["id"]
            prefix = f"runs/{identifier}/"
            latest = prefix + "latest.pt"
            if latest not in manifest:
                runs[identifier] = {"status": "not_started", "targets": 0}
                continue
            chunks = [
                e
                for e in events
                if e.get("type") == "chunk_result" and e["run"] == identifier
            ]
            if not chunks:
                initial = [
                    e
                    for e in events
                    if e.get("type") == "initial_drive_verified"
                    and e["run"] == identifier
                ]
                if (
                    not initial
                    or initial[-1]["hashes"]["latest.pt"] != manifest[latest]
                ):
                    raise ValueError("No matching initial receipt")
                runs[identifier] = {
                    "status": "initialized_only",
                    "targets": 0,
                    "checkpoint_sha256": manifest[latest],
                }
                continue
            last = chunks[-1]
            if last["checkpoint_sha256"] != manifest[latest]:
                raise ValueError("Latest checkpoint/last event differ")
            rows = [
                json.loads(line)
                for line in archive.read(prefix + "metrics.jsonl").splitlines()
                if line.strip()
            ]
            targets, inputs = 0, 0
            per_stage = {s["name"]: 0 for s in plan["config"]["stages"]}
            for update, row in enumerate(rows, 1):
                delta = row["batch_targets"]
                if type(delta) is not int or delta <= 0 or row["update"] != update:
                    raise ValueError("Invalid/noncontiguous update")
                targets += delta
                inputs += row["input_tokens"]
                per_stage[row["stage"]] += delta
                if (
                    row["targets"] != targets
                    or row["stage_targets"] != per_stage[row["stage"]]
                ):
                    raise ValueError("Target accounting mismatch")
                for key in (
                    "ce",
                    "grad_norm_before_clip",
                    "learning_rate",
                    "train_seconds",
                ):
                    if not math.isfinite(row[key]) or row[key] < 0:
                        raise ValueError("Invalid objective/gradient/time/rate")
            stats = last["stats"]
            if (
                stats["updates"] != len(rows)
                or stats["targets"] != targets
                or stats["input_tokens"] != inputs
            ):
                raise ValueError("Run stats and metrics differ")
            for stage in plan["config"]["stages"]:
                if per_stage[stage["name"]] > stage["targets"]:
                    raise ValueError("Stage exposure over budget")
            if last["complete"] != all(
                per_stage[s["name"]] == s["targets"] for s in plan["config"]["stages"]
            ):
                raise ValueError("Completion differs from exact exposure")
            if last["complete"] and prefix + "final.pt" not in manifest:
                raise ValueError("Missing completed checkpoint")
            runs[identifier] = {
                "complete": last["complete"],
                "stats": stats,
                "per_stage": per_stage,
                "metric_rows_verified": len(rows),
                "latest_sha256": manifest[latest],
                "final_sha256": manifest.get(prefix + "final.pt"),
                "last_peak_allocated_bytes": last["peak_allocated_bytes"],
            }
    return {
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "archive_sha256": expected_sha256,
        "archive_bytes": Path(path).stat().st_size,
        "members_verified": len(manifest),
        "plan_id": plan_id,
        "runs": runs,
        "checkpoint_pickle_loaded": False,
        "optimizer_updates_in_verification": 0,
        "scope": "byte integrity and log accounting; cloud readback provenance and scientific validity require separate evidence",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--plan-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = verify(args.archive, args.sha256, args.plan_id)
    with Path(args.output).open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
