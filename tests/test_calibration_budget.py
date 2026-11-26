"""No optimizer: cap reservations and reject ambiguous concurrent recovery."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_q3a_calibration import reserve_invocation

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
