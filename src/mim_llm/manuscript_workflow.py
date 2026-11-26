"""Prevent LaTeX builds before a paper's real experimental phases are complete."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

PHASES = ("data_collection", "training", "evaluation", "analysis")


def require_results_before_build(paper: str, root: Path) -> None:
    """Check readiness evidence, without running TeX or creating an approval step.

    Hashes establish artifact identity, not scientific validity. The research
    workflow must audit real phase completion before writing this receipt.
    """
    receipt = root / "artifacts/manuscript-readiness" / f"{paper}.json"
    reason = (
        f"LaTeX locked for {paper}: complete real data collection, training, "
        "evaluation and result analysis first (user instruction, 2026-11-26)."
    )
    if not receipt.is_file():
        raise SystemExit(reason)
    data = json.loads(receipt.read_text(encoding="utf-8"))
    if (
        data.get("paper") != paper
        or data.get("scientific_results_available") is not True
    ):
        raise SystemExit(reason)
    for phase in PHASES:
        record = data.get("phases", {}).get(phase, {})
        evidence = record.get("evidence", [])
        if record.get("status") != "complete" or not evidence:
            raise SystemExit(reason + f" Missing phase evidence: {phase}.")
        for item in evidence:
            path = Path(item["path"])
            if not path.is_absolute():
                path = root / path
            if not path.is_file():
                raise SystemExit(reason + f" Missing evidence file for {phase}.")
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for block in iter(lambda: handle.read(1 << 20), b""):
                    digest.update(block)
            if digest.hexdigest() != item.get("sha256"):
                raise SystemExit(reason + f" Changed evidence file for {phase}.")
