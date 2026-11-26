"""Fictional readiness receipts test a workflow lock; no TeX or model runs."""

import hashlib
import json
import runpy
from pathlib import Path

import pytest

from mim_llm.manuscript_workflow import PHASES, require_results_before_build


def fixture_receipt(tmp_path):
    evidence = tmp_path / "UNIT-only.txt"
    evidence.write_text(
        "FICTIONAL UNIT METADATA, NOT SCIENTIFIC RESULTS", encoding="utf-8"
    )
    receipt = tmp_path / "artifacts/manuscript-readiness/q3-a.json"
    receipt.parent.mkdir(parents=True)
    data = {
        "paper": "q3-a",
        "scientific_results_available": True,
        "phases": {
            phase: {
                "status": "complete",
                "evidence": [
                    {
                        "path": evidence.name,
                        "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
                    }
                ],
            }
            for phase in PHASES
        },
    }
    receipt.write_text(json.dumps(data), encoding="utf-8")
    return receipt, data, evidence


def test_no_real_result_receipt_stays_locked(tmp_path):
    for paper in ("q3-a", "q3-b", "q3-c", "q1"):
        with pytest.raises(SystemExit, match="LaTeX locked"):
            require_results_before_build(paper, tmp_path)


def test_every_phase_and_real_result_declaration_required(tmp_path):
    path, data, _ = fixture_receipt(tmp_path)
    require_results_before_build("q3-a", tmp_path)
    data["scientific_results_available"] = False
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(SystemExit, match="LaTeX locked"):
        require_results_before_build("q3-a", tmp_path)
    data["scientific_results_available"] = True
    data["phases"]["training"]["status"] = "pending"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(SystemExit, match="Missing phase evidence: training"):
        require_results_before_build("q3-a", tmp_path)


def test_changed_evidence_cannot_silently_unlock_build(tmp_path):
    _, _, evidence = fixture_receipt(tmp_path)
    evidence.write_text("UNIT changed", encoding="utf-8")
    with pytest.raises(SystemExit, match="Changed evidence"):
        require_results_before_build("q3-a", tmp_path)


@pytest.mark.parametrize("script", ["build_papers.py", "build_q3a_jucs.py"])
def test_entrypoints_stop_before_any_compiler_access(monkeypatch, script):
    def forbidden(*args, **kwargs):
        raise AssertionError("Compiler access before real results")

    monkeypatch.setattr("shutil.which", forbidden)
    monkeypatch.setattr("subprocess.run", forbidden)
    monkeypatch.setattr("sys.argv", [script])
    with pytest.raises(SystemExit, match="LaTeX locked"):
        runpy.run_path(
            str(Path(__file__).resolve().parents[1] / "scripts" / script),
            run_name="__main__",
        )
