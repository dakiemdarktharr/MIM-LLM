"""Audit TRAIN support and illustrative rule edge cases without model inference.

This does not create or register a challenge benchmark, read held-out stories,
or adjudicate free prose. Counterexamples are mathematical development cases.
"""

import argparse
import itertools
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from mim_llm.foundation.codec import FrozenTokenizer
from mim_llm.foundation.plan import load_plan
from mim_llm.q3a import data
from mim_llm.q3a.io import (
    read_json,
    read_rows,
    sha256,
    signature,
    source_sha256,
    write_json,
)
from mim_llm.q3a_subword import objectives


def sufficient_blocker_mentions(facts):
    """Nonempty sets of actually absent necessary prerequisites explain waiting."""
    blockers = [
        name
        for name, present in (
            ("power_unavailable", facts["power_available"]),
            ("permission_missing", facts["permission"]),
        )
        if not present
    ]
    return [
        list(choice)
        for size in range(1, len(blockers) + 1)
        for choice in itertools.combinations(blockers, size)
    ]


def audit(dataset, plan_path):
    directory = Path(dataset)
    manifest = read_json(directory / "manifest.json")
    if (
        signature({k: v for k, v in manifest.items() if k != "dataset_id"})
        != manifest["dataset_id"]
    ):
        raise ValueError("Dataset manifest changed")
    if manifest["generator_code_sha256"] != source_sha256(data.__file__):
        raise ValueError("Dataset generator differs from the recorded source")
    train = directory / "train.jsonl"
    if sha256(train) != manifest["sha256"][train.name]:
        raise ValueError("Training bytes changed")
    rows = read_rows(train)
    if len(rows) != manifest["counts"]["train"] or any(
        row["split"] != "train" for row in rows
    ):
        raise ValueError("Require the declared training split only")
    counts = {role: Counter() for role in data.ROLES}
    equality = {role: 0 for role in data.ROLES}
    depths = Counter()
    for row in rows:
        data.validate_bundle(row)
        depths[row["depth"]] += 1
        for role in data.ROLES:
            scenario = row["scenarios"][role]
            f = scenario["facts"]
            counts[role][
                f"power_{int(f['power_available'])}_permission_{int(f['permission'])}"
            ] += 1
            equality[role] += (
                scenario["world"]["power_return"] == scenario["world"]["deadline"]
            )
        if row["scenarios"]["base"]["facts"] != row["scenarios"]["noop"]["facts"]:
            raise ValueError("Existing no-op must preserve all declared tracked facts")

    # Fully specified, invented development worlds; not held-out source stories.
    base = {
        "initial_holder": "Lan",
        "transfers": ["Huy", "Mai"],
        "distractor": "An",
        "deadline": 540,
        "power_return": 545,
        "permission": False,
        "background_clock": 720,
        "attempted_receiver": None,
    }
    table = []
    for offset, permission in itertools.product((-1, 0, 1), (False, True)):
        world = {**base, "power_return": 540 + offset, "permission": permission}
        facts = data.state(world)
        if facts["power_available"] != (offset <= 0) or (facts["action"] == "open") != (
            offset <= 0 and permission
        ):
            raise ValueError(
                "Legacy inclusive rule does not match its declared truth table"
            )
        table.append(
            {
                "restoration_offset_minutes": offset,
                "permission": permission,
                "power_available": facts["power_available"],
                "action": facts["action"],
                "cabinet": facts["cabinet"],
                "sufficient_waiting_blocker_mentions": sufficient_blocker_mentions(
                    facts
                ),
            }
        )

    changed = {**base, "power_return": 535}
    before, after = data.state(base), data.state(changed)
    changed_keys = [k for k in before if before[k] != after[k]]
    invariant_keys = [k for k in before if before[k] == after[k]]
    if changed_keys != ["power_available"] or before["action"] != after["action"]:
        raise ValueError("Expected an outcome-preserving prerequisite-change example")
    plan = load_plan(plan_path)
    tokenizer = FrozenTokenizer(plan["tokenizer"], plan["tokenizer_spec"])
    # Offer this deliberately invalid full-state no-op to the real component
    # contract. It must reject a power-invariance target, not silently train it.
    probe_case = {
        "scenarios": {
            role: {"world": world, "prompt": data.render(world, 0)}
            for role, world in (("base", base), ("noop", changed))
        }
    }
    checked = {}
    for key in objectives.QUESTIONS:
        try:
            encoded = objectives.probe_rows(
                tokenizer, probe_case, plan["config"]["context"], probe_key=key
            )
        except ValueError as error:
            if key != "power_available" or "changed its target" not in str(error):
                raise
            checked[key] = "rejected_changed_target_as_required"
        else:
            if key not in invariant_keys or len(encoded) != 2:
                raise ValueError("Changed probe target was accepted")
            checked[key] = "invariant_target_accepted"

    return {
        "utc": datetime.now(UTC).isoformat(),
        "purpose": "training-support and mathematical development audit, not a model result",
        "dataset_id": manifest["dataset_id"],
        "training_sha256": sha256(train),
        "training_source_groups": len(rows),
        "derived_roles_per_group": len(data.ROLES),
        "decision_condition_counts_by_role": {
            k: dict(sorted(v.items())) for k, v in counts.items()
        },
        "exact_deadline_worlds_by_role": equality,
        "source_depth_counts": {str(k): v for k, v in sorted(depths.items())},
        "existing_noops_preserve_all_tracked_facts": True,
        "legacy_inclusive_rule_development_truth_table": table,
        "tie_semantics": {
            "legacy_power_condition": "power_return <= deadline",
            "natural_language_requires_explicit_order_if_co_timed": True,
            "illustrative_alternative_power_condition": "power_return < deadline",
            "alternative_policy_implemented_or_added_to_data": False,
        },
        "outcome_preserving_development_counterexample": {
            "base_power_offset_minutes": 5,
            "edited_power_offset_minutes": -5,
            "permission_granted": False,
            "single_changed_input_field": "power_return",
            "changed_tracked_fact_keys": changed_keys,
            "preserved_tracked_fact_keys": invariant_keys,
            "action_before_and_after": "wait",
            "cabinet_before_and_after": "locked",
            "sufficient_waiting_reasons_before": sufficient_blocker_mentions(before),
            "sufficient_waiting_reasons_after": sufficient_blocker_mentions(after),
            "existing_probe_contract_observed": checked,
            "not_an_existing_valid_noop_bundle": True,
        },
        "foundation_plan_id": plan["plan_id"],
        "tokenizer_sha256": plan["tokenizer_spec"]["sha256"],
        "state_generator_source_sha256": source_sha256(data.__file__),
        "probe_source_sha256": source_sha256(objectives.__file__),
        "implementation_sha256": source_sha256(__file__),
        "model_loaded": False,
        "optimizer_updates": 0,
        "tokenizer_fit": False,
        "controlled_validation_test_rows_loaded": False,
        "foundation_plan_input_integrity_hashes_checked": True,
        "foundation_validation_rows_decoded_or_scored": False,
        "new_model_generations": 0,
        "human_labels": 0,
        "new_challenge_dataset_registered": False,
        "current_dataset_or_training_plan_changed": False,
        "limitations": [
            "Finite truth tables do not establish language-model reasoning or human annotation validity.",
            "Outcome preservation is not invariance of every prerequisite or every valid explanation.",
            "Any broader challenge needs a versioned support/rubric/analysis plan before model evaluation; the existing locked test is unchanged.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--foundation-plan", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if Path(args.output).exists():
        raise FileExistsError("Preserve existing audits; use a new output path")
    result = audit(args.dataset, args.foundation_plan)
    write_json(args.output, result)
    print(
        {
            "training_sources": result["training_source_groups"],
            "exact_deadline_counts": result["exact_deadline_worlds_by_role"],
            "dual_blocker_counts": {
                role: counts.get("power_0_permission_0", 0)
                for role, counts in result["decision_condition_counts_by_role"].items()
            },
            "probe_contract": result["outcome_preserving_development_counterexample"][
                "existing_probe_contract_observed"
            ],
            "primary_test_read": False,
            "optimizer_updates": 0,
        }
    )


if __name__ == "__main__":
    main()
