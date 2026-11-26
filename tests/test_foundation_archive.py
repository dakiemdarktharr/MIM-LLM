"""Independent verification must reject intact-hash but invalid exposure logs."""

import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

from mim_llm.q3a.io import sha256, signature

spec = importlib.util.spec_from_file_location(
    "foundation_verifier",
    Path(__file__).resolve().parents[1] / "scripts/verify_q3a_foundation_archive.py",
)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def fixture_archive(
    tmp_path,
    change=None,
    *,
    resource_annex=False,
    invocation_count=1,
    bad_annex_evidence=False,
):
    plan = {
        "runs": [{"id": "foundation-transformer-s0"}, {"id": "foundation-mingru-s0"}],
        "config": {
            "resource_cap": {"maximum_invocations": 8},
            "stages": [{"name": "lm", "targets": 2}, {"name": "sft", "targets": 1}],
        },
    }
    plan["plan_id"] = signature(plan)
    metric = [
        {
            "update": 1,
            "stage": "lm",
            "batch_targets": 2,
            "input_tokens": 2,
            "targets": 2,
            "stage_targets": 2,
            "ce": 1.0,
            "grad_norm_before_clip": 0.2,
            "learning_rate": 0.001,
            "train_seconds": 0.1,
        },
        {
            "update": 2,
            "stage": "sft",
            "batch_targets": 1,
            "input_tokens": 2,
            "targets": 3,
            "stage_targets": 1,
            "ce": 1.1,
            "grad_norm_before_clip": 0.3,
            "learning_rate": 0.001,
            "train_seconds": 0.1,
        },
    ]
    if change:
        change(metric)
    checkpoint = b"A verifier must not load this fake pickle"
    event = {
        "type": "chunk_result",
        "run": "foundation-transformer-s0",
        "checkpoint_sha256": hashlib.sha256(checkpoint).hexdigest(),
        "complete": True,
        "stats": {"updates": 2, "targets": 3, "input_tokens": 4},
        "peak_allocated_bytes": 100,
    }
    files = {
        "inputs/foundation_plan-fixture.json": json.dumps(plan).encode(),
        "foundation-budget.json": json.dumps(
            {"plan_id": plan["plan_id"], "invocations": [{"status": "finished"}]}
        ).encode(),
        "sessions/a-events.jsonl": (json.dumps(event) + "\n").encode(),
        "runs/foundation-transformer-s0/latest.pt": checkpoint,
        "runs/foundation-transformer-s0/final.pt": checkpoint,
        "runs/foundation-transformer-s0/metrics.jsonl": "".join(
            json.dumps(r) + "\n" for r in metric
        ).encode(),
    }
    if resource_annex:
        from mim_llm.q3a.io import read_json

        annex = read_json("configs/q3a/foundation_resource_annex.json")
        annex["base_plan_id"] = plan["plan_id"]
        annex["unchanged_resource_limits"] = {}
        blobs = {
            "assessment": b'{"fixture": "no real measurement"}',
            "profile": b'{"fixture": "no real profile"}',
        }
        for key, blob in blobs.items():
            name = "sessions/" + annex[key + "_filename"]
            files[name] = blob
            annex[key + "_sha256"] = hashlib.sha256(blob).hexdigest()
        if bad_annex_evidence:
            annex["assessment_sha256"] = "0" * 64
        annex.pop("annex_id")
        annex["annex_id"] = signature(annex)
        raw = json.dumps(annex).encode()
        files["inputs/foundation_resource_annex-fixture.json"] = raw
        files["foundation-budget.json"] = json.dumps(
            {
                "plan_id": plan["plan_id"],
                "invocations": [
                    {"status": "finished"} for _ in range(invocation_count)
                ],
                "resource_annex": {
                    "annex_id": annex["annex_id"],
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "effective_before_invocation": 2,
                },
            }
        ).encode()
    out = tmp_path / "evidence.zip"
    with zipfile.ZipFile(out, "x") as archive:
        for name, value in files.items():
            archive.writestr(name, value)
        archive.writestr(
            "SHA256SUMS.json",
            json.dumps(
                {
                    name: hashlib.sha256(value).hexdigest()
                    for name, value in files.items()
                }
            ),
        )
    return out, plan["plan_id"]


def test_foundation_archive_no_pickle_and_missing_run_not_complete(tmp_path):
    path, identifier = fixture_archive(tmp_path)
    result = verifier.verify(path, sha256(path), identifier)
    assert result["checkpoint_pickle_loaded"] is False
    assert result["runs"]["foundation-transformer-s0"]["per_stage"] == {
        "lm": 2,
        "sft": 1,
    }
    assert result["runs"]["foundation-mingru-s0"]["status"] == "not_started"


@pytest.mark.parametrize(
    "field,value",
    [("targets", 7), ("update", 9), ("grad_norm_before_clip", float("nan"))],
)
def test_valid_hashes_do_not_excuse_invalid_target_or_finite_accounting(
    tmp_path, field, value
):
    path, identifier = fixture_archive(
        tmp_path, lambda rows: rows[1].update({field: value})
    )
    with pytest.raises(ValueError):
        verifier.verify(path, sha256(path), identifier)


@pytest.mark.parametrize(
    "count,corrupt,passes", [(16, False, True), (17, False, False), (2, True, False)]
)
def test_archive_resource_annex_requires_evidence_and_enforces_extended_cap(
    tmp_path, count, corrupt, passes
):
    path, identifier = fixture_archive(
        tmp_path,
        resource_annex=True,
        invocation_count=count,
        bad_annex_evidence=corrupt,
    )
    if passes:
        assert (
            verifier.verify(path, sha256(path), identifier)["checkpoint_pickle_loaded"]
            is False
        )
    else:
        with pytest.raises(ValueError):
            verifier.verify(path, sha256(path), identifier)
