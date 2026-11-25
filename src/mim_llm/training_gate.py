"""Fail closed before model optimization or tokenizer fitting."""

from __future__ import annotations

import json
from pathlib import Path

POLICY = Path(__file__).resolve().parents[2] / "configs" / "training_permission.json"


class TrainingNotAuthorized(PermissionError):
    pass


def require_training_permission(
    operation: str, run_id: str | None = None, *, plan_id: str | None = None
) -> None:
    if operation not in {"model", "tokenizer"}:
        raise ValueError("Unknown training operation")
    if not POLICY.is_file():
        raise TrainingNotAuthorized("Training policy missing: training is denied.")
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    key = (
        "model_training_authorized"
        if operation == "model"
        else "tokenizer_fitting_authorized"
    )
    if policy.get(key) is not True:
        raise TrainingNotAuthorized(
            "Training is locked. Wait for the user's explicit new instruction."
        )
    if not run_id or run_id not in policy.get("authorized_run_ids", []):
        raise TrainingNotAuthorized("This exact run ID has not been authorized.")
    if plan_id is not None and plan_id not in policy.get("authorized_plan_ids", []):
        raise TrainingNotAuthorized("This exact plan has not been authorized.")
