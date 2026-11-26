"""Fictional UNIT fixtures only: no real reader judgments or model findings."""

import csv
import hashlib
import json
from pathlib import Path

import pytest

from mim_llm.q3a.evaluate import analyze, blind_packet
from mim_llm.q3a.io import (
    read_json,
    read_rows,
    signature,
    source_sha256,
    write_json,
    write_rows,
)
from mim_llm.q3a_reviewed_analysis import (
    QUALITY_RULE,
    VERSION,
    join_generations,
    reviewed_analyze,
    validate_panel,
    validate_selection,
)
from mim_llm.tokenizer import ByteTokenizer


def unit_files(tmp_path):
    rows = []
    for kind in ("mingru", "transformer"):
        for arm in ("A1", "A2"):
            for seed in (0, 1, 2):
                run = {
                    "id": f"UNIT-{arm}-{kind}-{seed}",
                    "kind": kind,
                    "arm": arm,
                    "seed": seed,
                }
                for source in ("UNIT-source-a", "UNIT-source-b"):
                    for role in ("base", "effective", "noop"):
                        text = "UNIT invented text. This is a fixture. No real person rated it."
                        row = {
                            "source_id": source,
                            "scenario_id": f"{source}/{role}",
                            "role": role,
                            "split": "validation",
                            "run": run,
                            "plan_id": "UNIT-plan",
                            "decode_seed": 17,
                            "checkpoint_sha256": hashlib.sha256(
                                run["id"].encode()
                            ).hexdigest(),
                            "prompt": "FICTIONAL UNIT INPUT",
                            "mandatory": {},
                            "expected_facts": {},
                            "world": {"deadline": 540},
                            "pairs": [
                                {
                                    "kind": "effective",
                                    "changed": ["action", "cabinet"],
                                    "preserved": ["holder"],
                                },
                                {
                                    "kind": "noop",
                                    "changed": [],
                                    "preserved": ["holder", "action", "cabinet"],
                                },
                            ],
                            "continuation": text,
                            "token_ids": ByteTokenizer().encode(text),
                            "valid_utf8": True,
                        }
                        row["generation_id"] = signature(
                            {
                                k: row[k]
                                for k in (
                                    "scenario_id",
                                    "run",
                                    "checkpoint_sha256",
                                    "decode_seed",
                                )
                            }
                        )
                        rows.append(row)
    generation_file = tmp_path / "UNIT-generations.jsonl"
    write_rows(generation_file, rows)
    packet = tmp_path / "UNIT-packet"
    blind_packet([generation_file], packet)
    key = read_rows(packet / "PRIVATE-key.jsonl")
    byid = {r["item_id"]: r for r in key}
    for name, fluency in (("a", 2), ("b", 4)):
        path = packet / f"reader-{name}.csv"
        with path.open(newline="", encoding="utf-8") as f:
            labels = list(csv.DictReader(f))
        for label in labels:
            correct = int(byid[label["item_id"]]["run"]["arm"] == "A1")
            label.update(
                rater_id=f"UNIT-reader-{name}",
                all_mandatory_correct=str(correct),
                contradiction="0",
                contradiction_type="none",
                format_3_to_5="1",
                coverage_fraction="1"
                if correct
                else ("0.25" if name == "a" else "0.75"),
                fluency_1_to_5=str(fluency),
                unclear="0",
                evidence="FICTIONAL UNIT TEST ONLY",
            )
            for field in ("holder", "action", "cabinet", "reason"):
                label[field + "_correct"] = str(correct)
        save_csv(path, labels)
    return (
        packet / "reader-a.csv",
        packet / "reader-b.csv",
        packet / "PRIVATE-key.jsonl",
        generation_file,
    )


def save_csv(path, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def replace_rows(path, rows):
    Path(path).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def run(files, **kwargs):
    a, b, key, generations = files
    return reviewed_analyze(a, b, key, [generations], draws=100, **kwargs)


def test_both_reader_quality_used_without_changing_primary(tmp_path):
    files = unit_files(tmp_path)
    legacy = analyze(*files[:3], draws=100)
    result = run(files)
    assert result["primary_results"] == legacy["primary_results"]
    assert result["all_three_training_seeds_present"]
    assert all(x["fluency"] == 3 for x in result["quality_summaries"])
    assert all(
        x["coverage"] == (1 if x["arm"] == "A1" else 0.5)
        for x in result["quality_summaries"]
    )
    assert result["analysis_provenance"]["primary_definition_changed"] is False
    assert result["analysis_provenance"]["complete_panel"]["source_clusters"] == 2


def test_explicit_adjudication_quality_and_hash_recorded(tmp_path):
    files = unit_files(tmp_path)
    with files[0].open(newline="", encoding="utf-8") as f:
        labels = list(csv.DictReader(f))
    for row in labels:
        row.update(
            rater_id="UNIT-adjudication", fluency_1_to_5="5", coverage_fraction="1"
        )
    final = tmp_path / "UNIT-adjudicated.csv"
    save_csv(final, labels)
    result = run(files, adjudicated=final)
    assert all(
        x["fluency"] == 5 and x["coverage"] == 1 for x in result["quality_summaries"]
    )
    assert (
        result["analysis_provenance"]["adjudication_sha256"]
        == hashlib.sha256(final.read_bytes()).hexdigest()
    )


def test_missing_whole_source_in_one_seed_is_rejected(tmp_path):
    files = unit_files(tmp_path)
    key = read_rows(files[2])
    incomplete = [
        r
        for r in key
        if not (r["run"]["seed"] == 1 and r["source_id"] == "UNIT-source-b")
    ]
    with pytest.raises(ValueError, match="Incomplete"):
        validate_panel(incomplete)


def test_declared_seed_or_backbone_cannot_disappear_entirely(tmp_path):
    files = unit_files(tmp_path)
    key = read_rows(files[2])
    with pytest.raises(ValueError, match="Incomplete"):
        validate_panel([r for r in key if r["run"]["seed"] != 2], seeds=[0, 1, 2])
    with pytest.raises(ValueError, match="Incomplete"):
        validate_panel(
            [r for r in key if r["run"]["kind"] == "mingru"],
            backbones=["mingru", "transformer"],
        )


def test_raw_generation_bijection_and_metadata_are_checked(tmp_path):
    files = unit_files(tmp_path)
    rows = read_rows(files[3])
    replace_rows(files[3], rows[:-1])
    with pytest.raises(ValueError, match="exact unique panel"):
        join_generations(read_rows(files[2]), [files[3]])
    rows[0]["source_id"] = "UNIT-mismatched-source"
    replace_rows(files[3], rows)
    with pytest.raises(ValueError, match="metadata differs"):
        join_generations(read_rows(files[2]), [files[3]])


def test_invalid_bytes_retained_and_writing_validity_separate(tmp_path):
    files = unit_files(tmp_path)
    rows = read_rows(files[3])
    for row in rows:
        row.update(token_ids=[258], continuation="\ufffd", valid_utf8=False)
    replace_rows(files[3], rows)
    result = run(files)
    assert all(x["clean_utf8_fraction"] == 0 for x in result["quality_summaries"])
    assert all(x["outputs"] == 6 for x in result["quality_summaries"])
    assert all(x["source_clusters"] == 2 for x in result["primary_results"])
    # Machine writing validity does not silently rewrite the supplied UNIT human judgments.
    assert (
        result["primary_results"] == analyze(*files[:3], draws=100)["primary_results"]
    )


def test_decode_mismatch_or_stale_validity_rejected(tmp_path):
    files = unit_files(tmp_path)
    rows = read_rows(files[3])
    rows[0]["continuation"] = "UNIT edited after generation"
    replace_rows(files[3], rows)
    with pytest.raises(ValueError, match="raw generated"):
        run(files)
    rows[0]["continuation"] = ByteTokenizer().decode(rows[0]["token_ids"])
    rows[0]["valid_utf8"] = False
    replace_rows(files[3], rows)
    with pytest.raises(ValueError, match="validity flag"):
        run(files)


def test_unresolved_logic_disagreement_keeps_primary_unavailable(tmp_path):
    files = unit_files(tmp_path)
    with files[1].open(newline="", encoding="utf-8") as f:
        labels = list(csv.DictReader(f))
    selected = next(r for r in labels if r["all_mandatory_correct"] == "1")
    selected.update(action_correct="0", all_mandatory_correct="0")
    save_csv(files[1], labels)
    result = run(files)
    assert result["adjudication_required"] and result["primary_results"] is None
    assert "quality_summaries" not in result


def test_blank_annotations_still_rejected(tmp_path):
    files = unit_files(tmp_path)
    with files[0].open(newline="", encoding="utf-8") as f:
        labels = list(csv.DictReader(f))
    labels[0]["rater_id"] = ""
    save_csv(files[0], labels)
    with pytest.raises(ValueError, match="rater"):
        run(files)


def test_test_selection_requires_prospective_analysis_version(tmp_path):
    from mim_llm import q3a_reviewed_analysis as module

    files = unit_files(tmp_path)
    rows = read_rows(files[3])
    plan = {
        "plan_id": "UNIT-plan",
        "dataset_id": "UNIT-data",
        "config": {"decoding": {"seeds": [17]}},
    }
    selection = {
        "selection_frozen": True,
        "test_results_used": False,
        "plan_id": "UNIT-plan",
        "dataset_id": "UNIT-data",
        "decoding": plan["config"]["decoding"],
        "checkpoints": {r["run"]["id"]: r["checkpoint_sha256"] for r in rows},
        "analysis_registration": {
            "plan_id": "UNIT-plan",
            "test_results_used": False,
            "primary_contrast": ["A1", "A2"],
            "smallest_useful_effect": 0.1,
            "gpu_hours_cap_per_study": 1,
            "sample_method_and_rationale": "FICTIONAL UNIT REGISTRATION",
            "test_arms": ["A1", "A2"],
            "analysis_version": VERSION,
            "analysis_source_sha256": source_sha256(module.__file__),
            "quality_aggregation": QUALITY_RULE,
            "complete_source_seed_grid_required": True,
            "text_validity_role": "secondary_writing_metric_human_format_remains_primary",
            "test_source_ids": ["UNIT-source-a", "UNIT-source-b"],
        },
    }
    with pytest.raises(ValueError, match="locked"):
        validate_selection(plan, None, rows)
    assert validate_selection(plan, selection, rows) == [
        "UNIT-source-a",
        "UNIT-source-b",
    ]
    selection["analysis_registration"]["analysis_source_sha256"] = "UNIT-wrong-hash"
    with pytest.raises(ValueError, match="Register this analysis"):
        validate_selection(plan, selection, rows)


def unit_cli_files(tmp_path, monkeypatch, split):
    """Exercise CLI contracts; plan loading itself is tested in test_q3a.py."""
    from mim_llm import q3a_reviewed_analysis as module

    files = unit_files(tmp_path)
    rows = read_rows(files[3])
    key = read_rows(files[2])
    for row in rows + key:
        row["split"] = split
    replace_rows(files[3], rows)
    replace_rows(files[2], key)
    sources = {}
    for row in rows:
        bundle = sources.setdefault(
            row["source_id"],
            {"source_id": row["source_id"], "scenarios": {}, "pairs": row["pairs"]},
        )
        bundle["scenarios"][row["role"]] = {
            "id": row["scenario_id"],
            "world": row["world"],
            "prompt": row["prompt"],
            "mandatory": row["mandatory"],
            "facts": row["expected_facts"],
        }
    write_rows(tmp_path / f"{split}.jsonl", sources.values())
    plan = {
        "plan_id": "UNIT-plan",
        "dataset_id": "UNIT-data",
        "data_dir": str(tmp_path),
        "config": {
            "seeds": [0, 1, 2],
            "backbones": ["mingru", "transformer"],
            "decoding": {"seeds": [17]},
        },
        "runs": [
            {**run, "phase": "post"}
            for run in {r["run"]["id"]: r["run"] for r in rows}.values()
        ],
    }
    # Add the declared phase to generation and key metadata as the real runner does.
    for row in rows:
        row["run"]["phase"] = "post"
        row["generation_id"] = signature(
            {
                k: row[k]
                for k in ("scenario_id", "run", "checkpoint_sha256", "decode_seed")
            }
        )
    byslot = {(r["run"]["id"], r["source_id"], r["role"]): r for r in rows}
    for item in key:
        row = byslot[(item["run"]["id"], item["source_id"], item["role"])]
        item.update(run=row["run"], generation_id=row["generation_id"])
    replace_rows(files[3], rows)
    replace_rows(files[2], key)
    monkeypatch.setattr(module, "load_plan", lambda path: plan)
    output = tmp_path / "UNIT-result.json"
    argv = [
        "UNIT-analysis",
        "--plan",
        "UNIT-plan.json",
        "--labels-a",
        str(files[0]),
        "--labels-b",
        str(files[1]),
        "--key",
        str(files[2]),
        "--generations",
        str(files[3]),
        "--draws",
        "100",
        "--output",
        str(output),
    ]
    return module, files, plan, output, argv


def test_cli_validation_writes_versioned_result_without_overwrite(
    tmp_path, monkeypatch
):
    module, _, _, output, argv = unit_cli_files(tmp_path, monkeypatch, "validation")
    monkeypatch.setattr("sys.argv", argv)
    module.main()
    result = read_json(output)
    assert result["analysis_provenance"]["training_plan_id"] == "UNIT-plan"
    assert result["analysis_provenance"]["selection_sha256"] is None
    assert result["analysis_provenance"]["complete_panel"]["items"] == 72
    with pytest.raises(FileExistsError):
        module.main()


def test_cli_test_needs_prospective_lock_and_declared_all_seeds(tmp_path, monkeypatch):
    module, files, plan, output, argv = unit_cli_files(tmp_path, monkeypatch, "test")
    monkeypatch.setattr("sys.argv", argv)
    with pytest.raises(ValueError, match="locked"):
        module.main()
    rows = read_rows(files[3])
    lock = {
        "selection_frozen": True,
        "test_results_used": False,
        "plan_id": plan["plan_id"],
        "dataset_id": plan["dataset_id"],
        "decoding": plan["config"]["decoding"],
        "checkpoints": {r["run"]["id"]: r["checkpoint_sha256"] for r in rows},
        "analysis_registration": {
            "plan_id": plan["plan_id"],
            "test_results_used": False,
            "primary_contrast": ["A1", "A2"],
            "smallest_useful_effect": 0.1,
            "gpu_hours_cap_per_study": 1,
            "sample_method_and_rationale": "FICTIONAL UNIT REGISTRATION",
            "analysis_version": VERSION,
            "analysis_source_sha256": source_sha256(module.__file__),
            "quality_aggregation": QUALITY_RULE,
            "complete_source_seed_grid_required": True,
            "text_validity_role": "secondary_writing_metric_human_format_remains_primary",
            "test_source_ids": ["UNIT-source-a", "UNIT-source-b"],
            "test_arms": ["A1", "A2"],
        },
    }
    selection = tmp_path / "UNIT-selection.json"
    write_json(selection, lock)
    argv.extend(["--selection", str(selection)])
    module.main()
    assert read_json(output)["all_three_training_seeds_present"]
    output.unlink()
    lock["analysis_registration"]["test_arms"].append("A0")
    write_json(selection, lock, replace=True)
    with pytest.raises(ValueError, match="Incomplete"):
        module.main()
    assert not output.exists()


@pytest.mark.parametrize("field", ["prompt", "scenario_id", "world"])
def test_cli_rejects_generation_changed_from_declared_source(
    tmp_path, monkeypatch, field
):
    module, files, _, output, argv = unit_cli_files(tmp_path, monkeypatch, "validation")
    rows = read_rows(files[3])
    rows[0][field] = {"deadline": 541} if field == "world" else "UNIT changed"
    rows[0]["generation_id"] = signature(
        {
            k: rows[0][k]
            for k in ("scenario_id", "run", "checkpoint_sha256", "decode_seed")
        }
    )
    key = read_rows(files[2])
    for item in key:
        if (item["run"], item["source_id"], item["role"]) == (
            rows[0]["run"],
            rows[0]["source_id"],
            rows[0]["role"],
        ):
            item["generation_id"] = rows[0]["generation_id"]
    replace_rows(files[2], key)
    replace_rows(files[3], rows)
    monkeypatch.setattr("sys.argv", argv)
    with pytest.raises(ValueError, match="declared source"):
        module.main()
    assert not output.exists()
