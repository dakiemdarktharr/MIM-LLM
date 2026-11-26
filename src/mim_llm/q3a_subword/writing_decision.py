"""Apply the frozen author-reader feasibility rule to genuine saved ratings.

This validates records and calculates a descriptive screen. It cannot verify
who produced a rating or establish independent human evaluation. Blank or
partial labels always leave the decision pending; they are never imputed.
"""

import csv
import math
import unicodedata
from collections import Counter
from pathlib import Path

from ..q3a.io import read_json, read_rows, sha256, source_sha256
from .writing_packet import FIELDS, checked_samples

RULE_SHA256 = "590471e3dc722b083e95473c6b3648b18aab7abf0c5746ad1e5d6358d4da7910"
BINARY = (
    "format_3_to_5",
    "follows_prefix",
    "new_event",
    "self_consistent",
    "unclear",
)


def normalized(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def bound_packet(directory, manifest, packet_directory):
    """Bind every hidden mapping and displayed text to the original generation."""
    rows, review = checked_samples(directory, manifest)
    root = Path(packet_directory)
    receipt = read_json(root / "receipt.json")
    public = read_rows(root / "packet.jsonl")
    key = read_rows(root / "PRIVATE-key.jsonl")
    if (
        receipt.get("review_id") != review["review_id"]
        or receipt.get("packet_sha256") != sha256(root / "packet.jsonl")
        or receipt.get("source_samples_sha256")
        != sha256(Path(directory) / "samples.jsonl")
        or len(public) != 34
        or len(key) != 34
    ):
        raise ValueError("Packet differs from the original complete review")
    observed = {r["item_id"]: r for r in public}
    keys = {r["item_id"]: r for r in key}
    if len(observed) != 34 or len(keys) != 34 or set(observed) != set(keys):
        raise ValueError("Duplicate or missing blinded item")
    originals = {(r["run_id"], r["condition"], r["source_id"]): r for r in rows}
    used = set()
    for item_id, mapping in keys.items():
        identity = (mapping["run_id"], mapping["condition"], mapping["source_id"])
        if identity in used or identity not in originals:
            raise ValueError("Wrong or duplicated hidden model mapping")
        used.add(identity)
        original = originals[identity]
        if any(mapping[k] != original[k] for k in mapping if k != "item_id") or any(
            observed[item_id][k] != original[k] for k in ("prompt", "continuation")
        ):
            raise ValueError("Displayed text or hidden mapping was replaced")
    return rows, review, keys, receipt


def read_ratings(path, expected):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(FIELDS):
            raise ValueError("Use the original author-reader CSV columns")
        records = list(reader)
    found, complete = set(), {}
    for record in records:
        if None in record or any(v is None for v in record.values()):
            raise ValueError("Malformed rating CSV")
        row = {k: v.strip() for k, v in record.items()}
        item_id = row["item_id"]
        if item_id not in expected or item_id in found:
            raise ValueError("Unknown or repeated rating item")
        found.add(item_id)
        # Partially filled rows remain pending, but reject invalid supplied
        # values rather than silently excluding an inconvenient rating.
        for field in BINARY:
            if row[field] and row[field] not in {"0", "1"}:
                raise ValueError("Binary ratings must be zero or one")
        if row["fluency_1_to_5"] and row["fluency_1_to_5"] not in set("12345"):
            raise ValueError("Fluency must be an integer from one to five")
        if row["elapsed_seconds"]:
            elapsed = float(row["elapsed_seconds"])
            if not math.isfinite(elapsed) or elapsed <= 0:
                raise ValueError("Record real positive finite reading time")
        if all(row[field] for field in FIELDS):
            complete[item_id] = row
    if len({row["rater_id"] for row in complete.values()}) > 1:
        raise ValueError("This frozen feasibility screen declares one author-reader")
    return complete


def decide(directory, manifest, packet_directory, labels, rule):
    if sha256(rule) != RULE_SHA256:
        raise ValueError("Do not change the prospective feasibility thresholds")
    policy = read_json(rule)
    rows, review, keys, packet_receipt = bound_packet(
        directory, manifest, packet_directory
    )
    if (
        policy["review_id"] != review["review_id"]
        or policy["foundation_plan_id"] != review["plan_id"]
        or policy["inference_backend"] != review["inference_backend"]
    ):
        raise ValueError("Rule belongs to a different foundation review")
    ratings = read_ratings(labels, keys)
    all_rated = len(ratings) == policy["require_all_samples_rated"]

    def joint(row):
        expected = policy["sample_joint_pass"]
        return (
            all(int(row[k]) == expected[k] for k in BINARY)
            and int(row["fluency_1_to_5"]) >= expected["minimum_fluency_1_to_5"]
        )

    summaries = {}
    for run in sorted({r["run_id"] for r in rows}):
        group = [
            r for r in rows if r["run_id"] == run and r["condition"] == "conditional"
        ]
        largest = max(Counter(normalized(r["continuation"]) for r in group).values())
        conditional = [
            ratings[item_id]
            for item_id, key in keys.items()
            if item_id in ratings
            and key["run_id"] == run
            and key["condition"] == "conditional"
        ]
        unconditional = [
            ratings[item_id]
            for item_id, key in keys.items()
            if item_id in ratings
            and key["run_id"] == run
            and key["condition"] == "unconditional"
        ]
        count = sum(joint(row) for row in conditional)
        unconditioned_pass = joint(unconditional[0]) if unconditional else None
        summaries[run] = {
            "conditional_rated": len(conditional),
            "conditional_joint_passes": count,
            "conditional_denominator": len(group),
            "unconditional_rated": bool(unconditional),
            "unconditional_joint_pass": unconditioned_pass,
            "largest_normalized_identical_conditional_group": largest,
            "screen_passed": (
                count >= policy["per_backbone_minimum_joint_passes"]
                and unconditioned_pass is True
                and largest
                <= policy["maximum_identical_conditional_output_group_per_backbone"]
            )
            if all_rated
            else None,
        }
    passed = all(r["screen_passed"] for r in summaries.values()) if all_rated else None
    return {
        "decision": "pending" if passed is None else ("pass" if passed else "fail"),
        "writing_screen_passed": passed,
        "complete_rating_records": len(ratings),
        "expected_records": 34,
        "by_run": summaries,
        "review_id": review["review_id"],
        "plan_id": review["plan_id"],
        "rule_sha256": sha256(rule),
        "labels_sha256": sha256(labels),
        "packet_sha256": packet_receipt["packet_sha256"],
        "private_key_sha256": sha256(Path(packet_directory) / "PRIVATE-key.jsonl"),
        "samples_sha256": sha256(Path(directory) / "samples.jsonl"),
        "implementation_sha256": source_sha256(__file__),
        "reader_provenance": "declared author-reader; authenticity needs a real human, not this validator",
        "independent_reader_validation": False,
        "primary_results": False,
        "post_training_authorized": False,
        "optimizer_updates": 0,
        "test_access": False,
    }
