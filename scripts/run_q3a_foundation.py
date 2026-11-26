"""One bounded foundation driver, with verified Drive copies and a hard ledger."""

import argparse
import json
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import torch
from run_q3a_colab import sync_run_files, verified_copy

from mim_llm.foundation.modeling import FoundationConfig, build_foundation
from mim_llm.foundation.plan import load_plan
from mim_llm.foundation.runner import execute
from mim_llm.q3a.io import read_json, sha256, write_json


@torch.inference_mode()
def paths_preflight(plan, device, *, lengths=None):
    """Real tokenizer IDs/context, no updates; full/cached/step/causality."""
    result = []
    for kind, info in plan["models"].items():
        torch.manual_seed(0)
        model = build_foundation(FoundationConfig(**info["config"])).to(device).eval()
        for length in lengths or (32, 128, 512, plan["config"]["context"]):
            ids = torch.randint(
                1, plan["tokenizer_spec"]["vocab_size"] - 1, (1, length), device=device
            )
            ids[0, 0] = plan["tokenizer_spec"]["bos_id"]
            dense = model(ids)[0]
            model.train()
            training_path = model.head(model.training_features(ids))
            model.eval()
            training_error = float((training_path - dense).abs().max())
            cached, _, state = model(ids[:, :-1], return_state=True)
            last = model(ids[:, -1:], state=state, return_state=True)[0]
            if last.shape[1] != 1:
                raise ValueError("Cached path shape differs")
            dense_error = float((torch.cat((cached, last), 1) - dense).abs().max())
            stepped, _, step_state = model(ids[:, :1], return_state=True)
            rows = [stepped]
            for t in range(1, length):
                logits, _, step_state = model(
                    ids[:, t : t + 1], state=step_state, return_state=True
                )
                rows.append(logits)
            step_error = float((torch.cat(rows, 1) - dense).abs().max())
            edited = ids.clone()
            edited[:, length // 2 :] = (edited[:, length // 2 :] + 3) % plan[
                "tokenizer_spec"
            ]["vocab_size"]
            future_error = float(
                (model(edited)[0][:, : length // 2] - dense[:, : length // 2])
                .abs()
                .max()
            )
            if max(dense_error, step_error, training_error) > 2e-4 or future_error != 0:
                raise ValueError(f"CUDA path mismatch: {kind}/{length}")
            result.append(
                {
                    "kind": kind,
                    "length": length,
                    "cached_error": dense_error,
                    "step_error": step_error,
                    "training_path_error": training_error,
                    "past_logit_error": future_error,
                }
            )
        del model
        if device.startswith("cuda"):
            torch.cuda.empty_cache()
    return {
        "plan_id": plan["plan_id"],
        "torch": str(torch.__version__),
        "gpu": torch.cuda.get_device_name() if device.startswith("cuda") else None,
        "optimizer_updates": 0,
        "tolerance": 2e-4,
        "cases": result,
    }


def export_evidence(drive, stamp):
    files = sorted(
        p
        for name in ("runs", "sessions", "inputs")
        for p in (drive / name).rglob("*")
        if p.is_file() and p.suffix != ".zip"
    )
    files += [drive / "foundation-budget.json"]
    local = Path("artifacts") / (stamp + "-foundation-evidence.zip")
    local.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(local, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        hashes = {}
        for file in files:
            name = file.relative_to(drive).as_posix()
            hashes[name] = sha256(file)
            archive.write(file, name)
        archive.writestr("SHA256SUMS.json", json.dumps(hashes, indent=2))
    digest = verified_copy(local, drive / "exports" / local.name)
    print(
        json.dumps(
            {
                "type": "evidence_archive_verified_DriveFS",
                "name": local.name,
                "sha256": digest,
                "bytes": local.stat().st_size,
                "members": len(files),
                "independent_cloud_readback_pending": True,
            }
        ),
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--drive", required=True)
    parser.add_argument("--wall-seconds", type=int, default=1100)
    args = parser.parse_args()
    torch.set_num_threads(2)
    plan = load_plan(args.plan)
    cap = plan["config"]["resource_cap"]
    if not 1 <= args.wall_seconds <= cap["seconds_per_invocation"]:
        raise ValueError("Shorter wall cap must stay within the plan maximum")
    wall_seconds = args.wall_seconds
    if not torch.cuda.is_available() or not any(
        x in torch.cuda.get_device_name() for x in ("T4", "L4")
    ):
        raise ValueError(
            "Only measured T4/L4 GPU settings are eligible for the first probe"
        )
    drive = Path(args.drive).resolve()
    if not Path("/content/drive/MyDrive").is_dir() or not drive.is_relative_to(
        Path("/content/drive/MyDrive").resolve()
    ):
        raise ValueError("Mount the authorized Drive")
    if drive.name != "20261126-foundation-" + plan["plan_id"][:12]:
        raise ValueError("Separate destination required; preserve old experiments")
    observation = read_json(drive / "resource-observation.json")
    if (
        observation.get("plan_id") != plan["plan_id"]
        or observation.get("gpu") != torch.cuda.get_device_name()
        or observation.get("ui_checked") is not True
        or not 0
        < observation.get("cu_per_hour", 0)
        <= cap["maximum_observed_cu_per_hour"]
        or observation.get("available_cu", 0) < cap["minimum_available_cu"]
    ):
        raise ValueError("Fresh real UI account/rate observation required")
    observed_at = datetime.fromisoformat(observation["utc"])
    if not 0 <= (datetime.now(UTC) - observed_at).total_seconds() < 1200:
        raise ValueError("UI resource observation older than twenty minutes")
    ledger_path = drive / "foundation-budget.json"
    ledger = (
        read_json(ledger_path)
        if ledger_path.exists()
        else {
            "plan_id": plan["plan_id"],
            "starting_available_cu": observation["available_cu"],
            "invocations": [],
        }
    )
    if (
        ledger["plan_id"] != plan["plan_id"]
        or len(ledger["invocations"]) >= cap["maximum_invocations"]
        or any(r["status"] == "reserved" for r in ledger["invocations"])
        or ledger["starting_available_cu"] - observation["available_cu"]
        >= cap["maximum_observed_balance_drop"]
    ):
        raise ValueError("Budget cap/unresolved invocation: no automatic extension")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    entry = {
        "index": len(ledger["invocations"]) + 1,
        "utc": stamp,
        "status": "reserved",
        "reserved_soft_driver_seconds": wall_seconds,
        "observation": observation,
    }
    ledger["invocations"].append(entry)
    write_json(ledger_path, ledger, replace=ledger_path.exists())
    sessions = drive / "sessions"
    sessions.mkdir(exist_ok=True)
    for name in (
        args.plan,
        "configs/training_permission.json",
        "BUNDLE-MANIFEST.json",
        __file__,
        "docs/Q3_A_FOUNDATION_PROTOCOL_20261126.vi.md",
    ):
        p = Path(name)
        verified_copy(p, drive / "inputs" / (p.stem + "-" + sha256(p)[:12] + p.suffix))
    if Path("source-bundle.zip").exists():
        verified_copy(
            "source-bundle.zip",
            drive
            / "inputs"
            / ("source-bundle-" + sha256("source-bundle.zip")[:12] + ".zip"),
        )
    output = Path("artifacts/foundation-runs")
    output.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    console = sessions / (stamp + "-events.jsonl")

    def event(**values):
        row = {"utc": datetime.now(UTC).isoformat(), **values}
        with console.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        print(json.dumps(row), flush=True)

    try:
        if entry["index"] == 1:
            check = paths_preflight(plan, "cuda")
            write_json(sessions / (stamp + "-paths.json"), check)
            event(type="nonupdating_preflight_passed", cases=len(check["cases"]))
        for run in plan["runs"]:
            identifier = run["id"]
            remote, local = drive / "runs" / identifier, output / identifier
            if not local.exists() and (remote / "latest.pt").exists():
                local.mkdir()
                for file in remote.iterdir():
                    if file.is_file() and file.name != "previous.pt":
                        verified_copy(file, local / file.name)
            if not (local / "latest.pt").exists():
                initial = execute(
                    args.plan, identifier, output, seconds_limit=0.000001, device="cuda"
                )
                if initial["stats"]["updates"] != 0:
                    raise ValueError("Expected zero-update initial checkpoint")
                event(
                    type="initial_drive_verified",
                    run=identifier,
                    hashes=sync_run_files(local, remote),
                )
            while time.perf_counter() - start < wall_seconds - 20:
                saved = torch.load(
                    local / "latest.pt", map_location="cpu", weights_only=True
                )
                if saved["complete"]:
                    break
                del saved
                result = execute(
                    args.plan,
                    identifier,
                    output,
                    seconds_limit=min(
                        120,
                        wall_seconds - 20 - (time.perf_counter() - start),
                    ),
                    device="cuda",
                    resume=True,
                )
                event(
                    type="chunk_result", **result, hashes=sync_run_files(local, remote)
                )
                if result["complete"]:
                    break
            if time.perf_counter() - start >= wall_seconds - 20:
                break
        entry["status"] = "finished"
    except BaseException as error:
        entry["status"] = "failed"
        entry["error"] = repr(error)
        for local in output.glob("foundation-*-s0"):
            sync_run_files(local, drive / "runs" / local.name)
        raise
    finally:
        entry["elapsed_seconds"] = time.perf_counter() - start
        write_json(ledger_path, ledger, replace=True)
        export_evidence(drive, stamp)
        event(
            type="stopped",
            status=entry["status"],
            seconds=entry["elapsed_seconds"],
            next="Review measured speed/VRAM/CU before another driver; no post-matrix/test",
        )
        # Release only after verified Drive copies/archive; frontend may disconnect.
        from google.colab import runtime

        runtime.unassign()


if __name__ == "__main__":
    main()
