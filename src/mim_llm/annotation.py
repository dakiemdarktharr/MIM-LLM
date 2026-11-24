"""Two-reader agreement and explicit human adjudication.

This module never creates judgments. It validates and combines judgments
entered independently by people.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .evaluation import read_jsonl, write_jsonl

JUDGMENT_FIELDS = (
    "all_required",
    "contradiction",
    "concrete_event",
    "sentence_count_ok",
    "counterfactual_correct",
    "invariant_correct",
    "self_event_consistent",
    "self_event_state_after_first",
    "fluency_1_to_5",
    "coverage_0_to_1",
    "error_type",
)


def _indexed(path: str) -> dict[str, dict[str, Any]]:
    rows = read_jsonl(path)
    indexed = {row["anonymous_id"]: row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError(f"Duplicate anonymous IDs in {path}")
    return indexed


def reader_agreement(rater_a: str, rater_b: str) -> dict[str, Any]:
    a, b = _indexed(rater_a), _indexed(rater_b)
    if a.keys() != b.keys() or not a:
        raise ValueError("Reader packets must contain the same nonempty IDs")
    output: dict[str, Any] = {"samples": len(a), "fields": {}}
    for field in JUDGMENT_FIELDS:
        pairs = [(a[key].get(field), b[key].get(field)) for key in a]
        pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
        if not pairs:
            continue
        observed = sum(x == y for x, y in pairs) / len(pairs)
        result: dict[str, Any] = {"rated": len(pairs), "exact_agreement": observed}
        if all(type(x) is bool and type(y) is bool for x, y in pairs):
            pa = sum(x for x, _ in pairs) / len(pairs)
            pb = sum(y for _, y in pairs) / len(pairs)
            expected = pa * pb + (1 - pa) * (1 - pb)
            result["cohen_kappa"] = (
                (observed - expected) / (1 - expected) if expected < 1 else None
            )
        output["fields"][field] = result
    return output


def make_adjudication_packet(rater_a: str, rater_b: str, output: str) -> dict[str, int]:
    a, b = _indexed(rater_a), _indexed(rater_b)
    if a.keys() != b.keys() or not a:
        raise ValueError("Reader packets must contain the same nonempty IDs")
    if Path(output).exists():
        raise FileExistsError(output)
    rows = []
    disagreements = 0
    for key in sorted(a):
        row = dict(a[key])
        conflicts = {}
        for field in JUDGMENT_FIELDS:
            if a[key].get(field) != b[key].get(field):
                conflicts[field] = {
                    "reader_a": a[key].get(field),
                    "reader_b": b[key].get(field),
                }
                row[field] = None
        disagreements += len(conflicts)
        row["conflicts_to_adjudicate"] = conflicts
        row["notes"] = ""
        rows.append(row)
    write_jsonl(output, rows)
    return {"samples": len(rows), "conflicting_fields": disagreements}


def finalize_adjudication(packet: str, output: str) -> None:
    if Path(output).exists():
        raise FileExistsError(output)
    rows = read_jsonl(packet)
    for row in rows:
        for field in row.pop("conflicts_to_adjudicate", {}):
            if row.get(field) is None:
                raise ValueError(
                    f"Unresolved human adjudication: {row['anonymous_id']} {field}"
                )
    write_jsonl(output, rows)
