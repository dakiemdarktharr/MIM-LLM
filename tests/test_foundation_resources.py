"""Resource amendments preserve the learning plan and hard CU limits."""

import copy

import pytest

from mim_llm.q3a.io import read_json, signature
from mim_llm.q3a_subword.resources import check_ledger_annex, resource_cap


def declared():
    return read_json("configs/q3a/foundation_plan.json"), read_json(
        "configs/q3a/foundation_resource_annex.json"
    )


def resign(a):
    a.pop("annex_id", None)
    a["annex_id"] = signature(a)
    return a


def test_resource_annex_only_changes_driver_count():
    plan, annex = declared()
    cap = resource_cap(plan, annex)
    assert cap["maximum_invocations"] == 16
    original = plan["config"]["resource_cap"]
    assert original["maximum_invocations"] == 8
    assert {k: v for k, v in cap.items() if k != "maximum_invocations"} == {
        k: v for k, v in original.items() if k != "maximum_invocations"
    }
    assert resource_cap(plan) == original
    for key, value in [
        ("maximum_invocations", 17),
        ("learning_plan_changed", True),
        ("test_released", True),
        ("purchases_authorized", True),
        ("base_plan_id", "other"),
    ]:
        bad = copy.deepcopy(annex)
        bad[key] = value
        with pytest.raises(ValueError, match="unauthorized"):
            resource_cap(plan, resign(bad))
    bad = copy.deepcopy(annex)
    bad["unchanged_resource_limits"]["maximum_observed_balance_drop"] = 20
    with pytest.raises(ValueError, match="unauthorized"):
        resource_cap(plan, resign(bad))


def test_resource_ledger_cannot_add_annex_retroactively_or_drop_it():
    _, annex = declared()
    ledger = {"invocations": [{"index": 1}]}
    check_ledger_annex(ledger, annex, "fixture-sha")
    assert ledger["resource_annex"]["effective_before_invocation"] == 2
    ledger["invocations"].append({"index": 2})
    check_ledger_annex(ledger, annex, "fixture-sha")
    with pytest.raises(ValueError, match="omitted"):
        check_ledger_annex(ledger, None)
    with pytest.raises(ValueError, match="changed"):
        check_ledger_annex(ledger, annex, "different-file-sha")
    ledger.pop("resource_annex")
    with pytest.raises(ValueError, match="prospectively"):
        check_ledger_annex(ledger, annex, "fixture-sha")
