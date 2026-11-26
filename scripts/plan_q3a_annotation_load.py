"""Estimate annotation work from a declared plan; never create reader labels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def estimate(plan, source_counts, *, minutes_per_output=2.0, readers=2):
    if minutes_per_output <= 0 or readers < 2:
        raise ValueError("Positive time and two independent readers required")
    post = [r for r in plan["runs"] if r["phase"] == "post"]
    primary = [r for r in post if r["arm"] in plan["config"]["primary_contrast"]]
    decoding = len(plan["config"]["decoding"]["seeds"])
    roles = ("base", "effective", "noop")
    rows = []
    for sources in source_counts:
        if sources < 1:
            raise ValueError("At least one source is required")
        values = {"source_clusters": sources}
        for name, runs in [("primary", primary), ("all_arms", post)]:
            outputs = sources * len(runs) * decoding * len(roles)
            values[name + "_outputs"] = outputs
            values[name + "_reader_hours"] = outputs * readers * minutes_per_output / 60
        rows.append(values)
    return {
        "plan_id": plan["plan_id"],
        "evaluated_roles": list(roles),
        "post_runs": len(post),
        "primary_runs": len(primary),
        "decode_seeds": decoding,
        "readers": readers,
        "minutes_per_output_assumed_not_measured": minutes_per_output,
        "excludes": "training readers, semantic/source audit, adjudication and naturalistic transfer",
        "is_power_analysis": False,
        "labels_created": False,
        "scenarios": rows,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", required=True)
    p.add_argument("--sources", nargs="+", type=int, default=[12, 24, 48, 96, 400])
    p.add_argument("--minutes-per-output", type=float, default=2.0)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    result = estimate(plan, a.sources, minutes_per_output=a.minutes_per_output)
    out = Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as f:
        f.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
