"""Run one of at most three bounded calibration drivers and preserve evidence.

The ledger counts a reserved/crashed invocation against the cap. It does not
measure billed CU or authorize any post-training. Run from a dedicated bundle.
"""

import argparse
import json
import subprocess
import sys
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import torch
from run_q3a_colab import verified_copy

from mim_llm.q3a.io import read_json, sha256, write_json
from mim_llm.q3a.plan import load_plan


def reserve_invocation(path, plan_id):
    path = Path(path)
    ledger = (
        read_json(path)
        if path.exists()
        else {
            "plan_id": plan_id,
            "maximum_invocations": 3,
            "seconds_per_invocation": 1100,
            "invocations": [],
        }
    )
    if (
        ledger["plan_id"] != plan_id
        or ledger["maximum_invocations"] != 3
        or ledger["seconds_per_invocation"] != 1100
    ):
        raise ValueError("Wrong calibration budget ledger")
    if len(ledger["invocations"]) >= 3:
        raise ValueError(
            "Three-invocation calibration cap reached; no automatic extension"
        )
    if any(r["status"] == "reserved" for r in ledger["invocations"]):
        raise ValueError(
            "Prior invocation unresolved; reconcile real remote state before another launch"
        )
    ledger["invocations"].append(
        {
            "index": len(ledger["invocations"]) + 1,
            "utc": datetime.now(UTC).isoformat(),
            "status": "reserved",
            "reserved_driver_seconds": 1100,
        }
    )
    write_json(path, ledger, replace=path.exists())
    return ledger


def export_evidence(drive, stamp):
    drive = Path(drive)
    members = []
    for name in ("inputs", "sessions", "inspections"):
        members += [
            p
            for p in (drive / name).rglob("*")
            if p.is_file() and p.name != "source-bundle.zip"
        ]
    members += [drive / "calibration-budget.json"]
    for folder in (drive / "runs").glob("warmup-*-s0"):
        members += [p for p in folder.iterdir() if p.suffix in {".json", ".jsonl"}]
        chosen = folder / "final.pt"
        if not chosen.exists():
            chosen = folder / "latest.pt"
        if chosen.is_file():
            members.append(chosen)
    members = sorted(set(members))
    hashes = {p.relative_to(drive).as_posix(): sha256(p) for p in members}
    local = Path("artifacts") / (stamp + "-calibration-evidence.zip")
    local.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(local, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for p in members:
            archive.write(p, p.relative_to(drive).as_posix())
        archive.writestr("SHA256SUMS.json", json.dumps(hashes, indent=2))
    digest = verified_copy(local, drive / "exports" / local.name)
    print(
        json.dumps(
            {
                "type": "evidence_archive_verified_DriveFS",
                "file": local.name,
                "bytes": local.stat().st_size,
                "sha256": digest,
                "members": len(members),
                "independent_cloud_readback_pending": True,
            }
        ),
        flush=True,
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", required=True)
    p.add_argument("--drive", required=True)
    a = p.parse_args()
    plan = load_plan(a.plan)
    if (
        plan["config"].get("study") != "q3a-calibration2-seed0-only"
        or plan["config"]["warmup_targets"] != 50_000_000
    ):
        raise ValueError("Require prospectively declared calibration2 plan")
    if not torch.cuda.is_available() or not any(
        kind in torch.cuda.get_device_name() for kind in ("T4", "L4")
    ):
        raise RuntimeError("Calibration allows T4 or the declared L4 fallback only")
    drive = Path(a.drive).resolve()
    if (
        not drive.is_relative_to(Path("/content/drive/MyDrive").resolve())
        or not Path("/content/drive/MyDrive").is_dir()
    ):
        raise RuntimeError("Mount the authorized Drive first")
    if drive.name != "20261126-calibration2-" + plan["plan_id"][:12]:
        raise ValueError(
            "Use the separate calibration2 destination, preserving the old pilot"
        )
    drive.mkdir(parents=True, exist_ok=True)
    observation = read_json(drive / "resource-observation.json")
    if (
        observation.get("plan_id") != plan["plan_id"]
        or observation.get("observed_gpu_name") != torch.cuda.get_device_name()
        or observation.get("UI_rate_checked_before_training") is not True
        or not 0 < observation.get("UI_approximate_CU_per_hour", 0) <= 6
        or observation.get("UI_available_CU", 0) < 10
    ):
        raise ValueError(
            "Record real UI GPU/CU/rate before calibration; do not buy credits"
        )
    ledger_path = drive / "calibration-budget.json"
    if (
        ledger_path.exists()
        and read_json(ledger_path).get("gpu_name") != torch.cuda.get_device_name()
    ):
        raise ValueError("Keep both new warmups on the same GPU class")
    ledger = reserve_invocation(ledger_path, plan["plan_id"])
    ledger["gpu_name"] = torch.cuda.get_device_name()
    ledger["resource_observation"] = observation
    write_json(ledger_path, ledger, replace=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    sessions = drive / "sessions"
    sessions.mkdir(exist_ok=True)
    for file in (
        "docs/Q3_A_CALIBRATION2_PROTOCOL.vi.md",
        __file__,
        "scripts/inspect_q3a_warmup.py",
        "scripts/inspect_q3a_more_prefixes.py",
    ):
        verified_copy(file, drive / "inputs" / Path(file).name)
    verified_copy(
        drive / "resource-observation.json",
        sessions / (stamp + "-resource-observation.json"),
    )
    start = time.perf_counter()
    status = None
    process = None
    driver_error = None
    try:
        with (sessions / (stamp + "-console.txt")).open("x", encoding="utf-8") as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-u",
                    "scripts/run_q3a_colab.py",
                    "--plan",
                    a.plan,
                    "--drive",
                    str(drive),
                    "--phase",
                    "warmup",
                    "--wall-seconds",
                    "1100",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                bufsize=1,
            )
            for line in process.stdout:
                print(line, end="", flush=True)
                log.write(line)
                log.flush()
            status = process.wait()
    except BaseException as error:  # noqa: BLE001 - stop child, preserve ledger, then re-raise
        driver_error = error
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        if process is not None:
            status = process.returncode
    finally:
        ledger["invocations"][-1].update(
            status="finished" if status == 0 else "failed_or_interrupted",
            returncode=status,
            driver_observed_seconds=time.perf_counter() - start,
        )
        write_json(ledger_path, ledger, replace=True)
    try:
        if driver_error is not None:
            raise driver_error
        if status != 0:
            raise RuntimeError(
                "Training driver failed; retained logs/checkpoints need audit"
            )
        complete = all(
            (drive / "runs" / f"warmup-{kind}-s0" / "final.pt").is_file()
            for kind in ("mingru", "transformer")
        )
        if complete:
            destination = drive / "inspections"
            destination.mkdir(exist_ok=True)
            for script, label in (
                ("inspect_q3a_warmup.py", "warmup-validation"),
                ("inspect_q3a_more_prefixes.py", "more-prefixes"),
            ):
                with (destination / (stamp + "-" + label + ".console.txt")).open(
                    "x", encoding="utf-8"
                ) as log:
                    subprocess.run(
                        [
                            sys.executable,
                            "-u",
                            "scripts/" + script,
                            "--plan",
                            a.plan,
                            "--checkpoint-root",
                            "artifacts/colab-q3a-runs",
                            "--output",
                            str(destination / (stamp + "-" + label + ".jsonl")),
                        ],
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        check=True,
                    )
            print(
                "Both calibration warmups complete; fixed validation samples saved. No post-training launched.",
                flush=True,
            )
        else:
            print(
                "Calibration chunk persisted; inspect ledger and remaining budget before resuming.",
                flush=True,
            )
    finally:
        export_evidence(drive, stamp)


if __name__ == "__main__":
    main()
