"""No optimizer: cap reservations and reject ambiguous concurrent recovery."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_q3a_calibration import record_hardware, reserve_invocation

from mim_llm.q3a.io import write_json


def test_three_reservations_are_a_hard_cap(tmp_path):
    path = tmp_path / "budget.json"
    for i in range(3):
        ledger = reserve_invocation(path, "fixture-plan")
        assert ledger["invocations"][-1]["index"] == i + 1
        ledger["invocations"][-1]["status"] = "finished"
        write_json(path, ledger, replace=True)
    with pytest.raises(ValueError, match="cap reached"):
        reserve_invocation(path, "fixture-plan")


def test_ambiguous_previous_invocation_and_changed_plan_fail_closed(tmp_path):
    path = tmp_path / "budget.json"
    reserve_invocation(path, "fixture-plan")
    with pytest.raises(ValueError, match="unresolved"):
        reserve_invocation(path, "fixture-plan")
    with pytest.raises(ValueError, match="Wrong"):
        reserve_invocation(path, "different-plan")


def test_portable_resume_records_each_actual_gpu_without_relabeling_old_segment():
    ledger = {
        "gpu_name": "NVIDIA L4",
        "invocations": [
            {"index": 1, "status": "finished"},
            {"index": 2, "status": "reserved"},
        ],
    }
    record_hardware(ledger, "Tesla T4")
    assert ledger["initial_gpu_name"] == "NVIDIA L4"
    assert [r["gpu_name"] for r in ledger["invocations"]] == ["NVIDIA L4", "Tesla T4"]
    assert ledger["hardware_changed_across_segments"] is True
    assert ledger["gpu_history"] == ["NVIDIA L4", "Tesla T4"]
