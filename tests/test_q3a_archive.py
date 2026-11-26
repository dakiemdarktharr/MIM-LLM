"""Synthetic ZIPs test corruption detection; no model or scientific labels."""

import hashlib
import json
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_q3a_archive import digest_file, verify_archive


def make_fixture(path, failure=None):
    members = {}
    for kind in ("mingru", "transformer"):
        prefix = f"runs/warmup-{kind}-s0/"
        row = {
            "update": 1,
            "target_delta": 5,
            "targets": 5,
            "ce": 1.0,
            "objective": 1.0,
            "gradient_norm": 0.2,
            "seconds": 0.1,
        }
        if kind == "mingru" and failure == "nonfinite":
            row["objective"] = float("nan")
        if kind == "mingru" and failure == "accounting":
            row["targets"] = 6
        run = {
            "plan_id": "fixture-plan",
            "actual_parameters": 1,
            "run": {
                "id": f"warmup-{kind}-s0",
                "kind": kind,
                "seed": 0,
                "phase": "warmup",
                "targets": 5,
            },
            "stats": {"trained_targets": 5, "updates": 1},
            "complete": True,
        }
        members[prefix + "run.json"] = json.dumps(run).encode()
        members[prefix + "metrics.jsonl"] = (json.dumps(row) + "\n").encode()
        members[prefix + "final.pt"] = b"fixture-not-a-pickle"
    hashes = {k: hashlib.sha256(v).hexdigest() for k, v in members.items()}
    if failure == "member_hash":
        members["runs/warmup-mingru-s0/final.pt"] += b"changed"
    with zipfile.ZipFile(path, "x") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
        archive.writestr("SHA256SUMS.json", json.dumps(hashes))
    return digest_file(path)


def test_fixture_logs_verified_without_unpickling(tmp_path):
    path = tmp_path / "fixture.zip"
    digest = make_fixture(path)
    report = verify_archive(path, digest, "fixture-plan")
    assert report["members_verified"] == 6
    assert all(r["metric_rows_verified"] == 1 for r in report["runs"].values())
    assert report["checkpoint_pickle_loaded"] is False


@pytest.mark.parametrize(
    "failure,message",
    [
        ("member_hash", "Member hash mismatch"),
        ("accounting", "target sum mismatch"),
        ("nonfinite", "Nonfinite"),
    ],
)
def test_matching_archive_digest_does_not_hide_internal_errors(
    tmp_path, failure, message
):
    path = tmp_path / "fixture.zip"
    digest = make_fixture(path, failure)
    with pytest.raises(ValueError, match=message):
        verify_archive(path, digest, "fixture-plan")


def test_wrong_external_digest_and_plan_rejected(tmp_path):
    path = tmp_path / "fixture.zip"
    digest = make_fixture(path)
    with pytest.raises(ValueError, match="external receipt"):
        verify_archive(path, "0" * 64, "fixture-plan")
    with pytest.raises(ValueError, match="identity"):
        verify_archive(path, digest, "wrong-plan")
