"""Bounded Q3-A jobs; verify persistent checkpoint copies, never buy resources."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import torch

from mim_llm.q3a.io import sha256
from mim_llm.q3a.plan import load_plan
from mim_llm.q3a.runner import execute


def verified_copy(source, target, *, keep_previous=False):
    """Stage, reread and hash before replacing; Drive rename is not a transaction."""
    source, target = Path(source), Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    expected = sha256(source)
    if target.exists() and sha256(target) == expected:
        return expected
    temporary = target.with_name(target.name + ".uploading")
    shutil.copyfile(source, temporary)
    if sha256(temporary) != expected:
        raise OSError("Drive reread hash mismatch; previous checkpoint retained")
    if keep_previous and target.exists():
        verified_copy(target, target.with_name("previous.pt"))
    os.replace(temporary, target)
    if sha256(target) != expected:
        raise OSError("Published copy hash mismatch")
    return expected


def sync_run_files(folder, remote):
    """Keep previous.pt owned by remote latest rotation, not a stale restore."""
    folder, remote = Path(folder), Path(remote)
    hashes = {}
    for path in sorted(folder.glob("*")):
        if (
            path.is_file()
            and path.suffix in {".pt", ".json", ".jsonl"}
            and path.name != "previous.pt"
        ):
            hashes[path.name] = verified_copy(
                path, remote / path.name, keep_previous=path.name == "latest.pt"
            )
    previous = remote / "previous.pt"
    if previous.is_file():
        hashes["previous.pt"] = sha256(previous)
    return hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--drive", required=True)
    parser.add_argument("--phase", choices=["warmup", "contrast"], default="warmup")
    parser.add_argument("--wall-seconds", type=int, default=1200)
    args = parser.parse_args()
    torch.set_num_threads(2)
    if not torch.cuda.is_available():
        raise RuntimeError("A GPU runtime is required; do not silently train on CPU")
    if not 1 <= args.wall_seconds <= 1200:
        raise ValueError("Initial session soft cap: at most 20 minutes")
    drive = Path(args.drive).resolve()
    mount = Path("/content/drive/MyDrive")
    if not mount.is_dir() or not drive.is_relative_to(mount.resolve()):
        raise RuntimeError("Mount and verify the authorized Google Drive first")
    drive.mkdir(parents=True, exist_ok=True)
    probe = drive / "drive-write-probe.json"
    probe.write_text(
        json.dumps(
            {"utc": datetime.now(UTC).isoformat(), "purpose": "Q3-A persistence check"}
        )
    )
    assert json.loads(probe.read_text())["purpose"] == "Q3-A persistence check"
    plan = load_plan(args.plan)
    local = Path("artifacts/colab-q3a-runs")
    local.mkdir(parents=True, exist_ok=True)
    session = drive / "sessions"
    session.mkdir(exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    log = session / (stamp + "-" + args.phase + ".jsonl")

    def event(**values):
        values = {"utc": datetime.now(UTC).isoformat(), **values}
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(values) + "\n")
        print(json.dumps(values), flush=True)

    verified_copy(args.plan, drive / "inputs" / "plan.json")
    verified_copy(
        "configs/training_permission.json", drive / "inputs" / "permission.json"
    )
    verified_copy(
        "BUNDLE-MANIFEST.json",
        drive
        / "inputs"
        / ("BUNDLE-MANIFEST-" + sha256("BUNDLE-MANIFEST.json")[:12] + ".json"),
    )
    if Path("source-bundle.zip").exists():
        verified_copy(
            "source-bundle.zip",
            drive
            / "inputs"
            / ("source-bundle-" + sha256("source-bundle.zip")[:12] + ".zip"),
        )
    for file in [
        "docs/SCOPE_REVIEW_BEFORE_TRAIN_20261126.vi.md",
        "DATA_NOTICES.md",
        __file__,
    ]:
        source = Path(file)
        versioned = source.stem + "-" + sha256(source)[:12] + source.suffix
        verified_copy(source, drive / "inputs" / versioned)
    packages = subprocess.check_output(["python", "-m", "pip", "freeze"], text=True)
    (session / (stamp + "-packages.txt")).write_text(packages)
    jobs = (
        ["warmup-transformer-s0", "warmup-mingru-s0"]
        if args.phase == "warmup"
        else [
            f"{arm}-{kind}-s0"
            for kind in ("transformer", "mingru")
            for arm in ("A1", "A2")
        ]
    )
    event(
        type="session_start",
        plan_id=plan["plan_id"],
        gpu=torch.cuda.get_device_name(),
        phase=args.phase,
        jobs=jobs,
        soft_wall_seconds=args.wall_seconds,
        actual_parameters={
            k: v["actual_parameters"] for k, v in plan["models"].items()
        },
        note="CU meter must be observed in Colab UI; no inferred or purchased credits",
    )

    def sync_run(identifier):
        folder = local / identifier
        hashes = sync_run_files(folder, drive / "runs" / identifier)
        event(type="drive_sync_verified", run=identifier, sha256=hashes)

    started = time.perf_counter()
    for identifier in jobs:
        folder = local / identifier
        remote = drive / "runs" / identifier
        if not folder.exists() and (remote / "latest.pt").is_file():
            folder.mkdir()
            for p in remote.iterdir():
                if p.is_file() and p.suffix in {".pt", ".json", ".jsonl"}:
                    verified_copy(p, folder / p.name)
        if args.phase == "contrast":
            parent = next(r["parent"] for r in plan["runs"] if r["id"] == identifier)
            if not (local / parent / "final.pt").is_file():
                src = drive / "runs" / parent / "final.pt"
                if not src.is_file():
                    raise RuntimeError("Complete matching initialization is missing")
                verified_copy(src, local / parent / "final.pt")
        if not (folder / "latest.pt").exists():
            initialized = execute(
                args.plan, identifier, local, seconds_limit=0.000001, device="cuda"
            )
            if initialized["stats"]["updates"] != 0:
                raise RuntimeError("Expected a zero-update initialization checkpoint")
            sync_run(identifier)
            event(
                type="initial_checkpoint_verified_before_updates",
                run=identifier,
                checkpoint_sha256=initialized["checkpoint_sha256"],
            )
        while time.perf_counter() - started < args.wall_seconds:
            latest = folder / "latest.pt"
            if latest.exists():
                checkpoint = torch.load(latest, map_location="cpu", weights_only=True)
                if checkpoint["complete"]:
                    sync_run(identifier)
                    break
            remaining = args.wall_seconds - (time.perf_counter() - started)
            if remaining < 5:
                break
            event(type="chunk_start", run=identifier, resume=latest.exists())
            try:
                result = execute(
                    args.plan,
                    identifier,
                    local,
                    seconds_limit=min(120, remaining),
                    device="cuda",
                    resume=latest.exists(),
                )
            except BaseException as error:
                sync_run(identifier)
                event(type="job_error", run=identifier, error=repr(error))
                raise
            sync_run(identifier)
            event(
                type="chunk_result",
                run=identifier,
                complete=result["complete"],
                stats=result["stats"],
                checkpoint_sha256=result["checkpoint_sha256"],
                peak_allocated_bytes=result["peak_allocated_bytes"],
                invocation_seconds=result["invocation_seconds"],
                invocation_train_seconds=result["invocation_train_seconds"],
            )
            if result["complete"]:
                break
        else:
            break
        if time.perf_counter() - started >= args.wall_seconds:
            break
    event(
        type="session_stopped",
        elapsed_seconds=time.perf_counter() - started,
        next="Inspect real validation writing and resource use before expanding; test remains locked",
    )
    print("DRIVE_OUTPUT", drive, flush=True)


if __name__ == "__main__":
    main()
