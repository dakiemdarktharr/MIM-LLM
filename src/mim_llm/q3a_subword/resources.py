"""Prospective resource-only annex; never changes learning/checkpoint identity."""

from ..q3a.io import signature


def resource_cap(plan, annex=None):
    cap = dict(plan["config"]["resource_cap"])
    if annex is None:
        return cap
    if signature({k: v for k, v in annex.items() if k != "annex_id"}) != annex.get(
        "annex_id"
    ):
        raise ValueError("Resource annex digest mismatch")
    if (
        annex.get("base_plan_id") != plan["plan_id"]
        or annex.get("schema_version") != 1
        or annex.get("effective_before_invocation") != 2
        or annex.get("maximum_invocations_before") != cap["maximum_invocations"]
        or cap["maximum_invocations"] != 8
        or annex.get("maximum_invocations") != 16
        or annex.get("unchanged_resource_limits")
        != {k: v for k, v in cap.items() if k != "maximum_invocations"}
        or annex.get("learning_plan_changed") is not False
        or annex.get("purchases_authorized") is not False
        or annex.get("extra_studies_or_post_matrix_authorized") is not False
        or annex.get("test_released") is not False
        or annex.get("observed_balance_anchor_cu") != 597.61
        or annex.get("optimistic_remaining_seconds", 0)
        <= annex.get("original_remaining_seconds", 0)
    ):
        raise ValueError("Resource annex changes unauthorized limits or learning scope")
    cap["maximum_invocations"] = annex["maximum_invocations"]
    return cap


def check_ledger_annex(ledger, annex, annex_sha256=None):
    recorded = ledger.get("resource_annex")
    if annex is None:
        if recorded is not None:
            raise ValueError("Recorded resource annex cannot be silently omitted")
        return
    expected = {
        "annex_id": annex["annex_id"],
        "sha256": annex_sha256,
        "effective_before_invocation": 2,
    }
    if recorded is not None and recorded != expected:
        raise ValueError("Ledger resource annex changed")
    if recorded is None and len(ledger["invocations"]) != 1:
        raise ValueError("Annex must be recorded prospectively before invocation two")
    ledger["resource_annex"] = expected
