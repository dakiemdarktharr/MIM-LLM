"""Fictional evaluation fixtures; no real human judgments or model findings."""

import importlib

import pytest

from mim_llm.q3a.io import read_rows, write_rows
from mim_llm.q3bc.data import prepare
from mim_llm.q3bc.evaluate import analyze, blind_packet
from mim_llm.q3bc.report import results_table


@pytest.mark.parametrize("study", ["b", "c"])
def test_blank_labels_rejected_then_cluster_analysis_on_explicit_unit_fixtures(
    tmp_path, study
):
    rows = []
    left, right = ("B2", "B1") if study == "b" else ("C2", "C1")
    for arm in (left, right):
        for source in ("unit-source-a", "unit-source-b"):
            for panel in ("continuation",) if study == "b" else ("free", "fixed"):
                mandatory = (
                    {"location": "UNIT", "latest_update": "UNIT", "retention": "UNIT"}
                    if study == "b"
                    else {"actual_event_followup": "UNIT", "valid_explanation": "UNIT"}
                )
                rows.append(
                    {
                        "study": study,
                        "plan_id": "UNIT",
                        "source_id": source,
                        "split": "validation",
                        "run": {"kind": "mingru", "arm": arm, "seed": 0},
                        "decode_seed": 17,
                        "panel": panel,
                        "generation_id": f"UNIT-{arm}-{source}-{panel}",
                        "prompt": "UNIT FICTION",
                        "first_segment": None if study == "b" else "UNIT FICTION",
                        "followup_prompt": None,
                        "continuation": "UNIT FICTION",
                        "mandatory": mandatory,
                    }
                )
    gens = tmp_path / "unit.jsonl"
    write_rows(gens, rows)
    packet = tmp_path / "packet"
    blind_packet([gens], packet)
    output = tmp_path / "analysis.json"
    with pytest.raises(ValueError, match="reader"):
        analyze(
            packet / "reader-a.jsonl",
            packet / "reader-b.jsonl",
            packet / "PRIVATE-key.jsonl",
            output,
            draws=100,
        )
    key = {r["item_id"]: r for r in read_rows(packet / "PRIVATE-key.jsonl")}
    for reader in ("a", "b"):
        path = packet / f"reader-{reader}.jsonl"
        labels = read_rows(path)
        for r in labels:
            correct = int(key[r["item_id"]]["run"]["arm"] == left)
            r.update(
                rater_id="UNIT-" + reader,
                propositions={k: correct for k in r["propositions"]},
                instructions_met=1,
                contradiction=0,
                contradiction_type="none",
                format_3_to_5=1,
                new_event=1,
                prefix_valid=1,
                followup_consistent=correct,
                unclear=0,
                coverage_fraction=1,
                fluency_1_to_5=3,
                evidence="FICTIONAL UNIT TEST",
            )
        path.unlink()
        write_rows(path, labels)
    result = analyze(
        packet / "reader-a.jsonl",
        packet / "reader-b.jsonl",
        packet / "PRIVATE-key.jsonl",
        output,
        draws=100,
    )
    assert all(
        r["effect"] == 1 and r["source_clusters"] == 2
        for r in result["primary_results"]
    )
    assert result["split"] == "validation"
    with pytest.raises(ValueError):
        results_table(output, tmp_path / "not-a-paper-result.tex")


def test_c_free_history_preserves_raw_ids_even_when_parser_cannot_read_it(
    tmp_path, monkeypatch
):
    from mim_llm.tokenizer import ByteTokenizer

    module = importlib.import_module("mim_llm.q3bc.evaluate")
    t = ByteTokenizer()
    d = tmp_path / "c"
    prepare("c", d, train_sources=1, validation_sources=1, test_sources=1)
    p = {
        "study": "c",
        "data_dir": str(d),
        "plan_id": "UNIT",
        "config": {
            "decoding": {
                "seeds": [17],
                "first_tokens": 256,
                "max_new_tokens": 384,
                "temperature": 0.8,
                "top_k": 40,
            }
        },
    }
    monkeypatch.setattr(module, "load_plan", lambda *a, **k: p)
    monkeypatch.setattr(
        module,
        "load_model",
        lambda *a: ("UNIT-MODEL", {"run": {"kind": "mingru", "arm": "C2", "seed": 0}}),
    )
    raw = [258, 260 - 3, 30]
    calls = []
    monkeypatch.setattr(
        module,
        "generate",
        lambda *a, **k: {
            "continuation": "unparsed UNIT first segment",
            "token_ids": raw,
            "valid_utf8": False,
        },
    )

    def second(model, tokenizer, prefix, **kwargs):
        calls.append(prefix)
        return {"continuation": "UNIT suffix", "token_ids": [80], "valid_utf8": True}

    monkeypatch.setattr(module, "generate_from_ids", second)
    ckpt = tmp_path / "unit-checkpoint.bin"
    ckpt.write_bytes(b"UNIT ONLY")
    out = tmp_path / "out.jsonl"
    module.generate_panel("UNIT", ckpt, out)
    row = read_rows(d / "validation.jsonl")[0]
    assert calls[0] == t.encode(row["prompt"], bos=True) + raw + t.encode(
        row["followup"]
    )
    generated = read_rows(out)
    assert {r["panel"] for r in generated} == {"free", "fixed"}
    assert next(r for r in generated if r["panel"] == "free")["first_token_ids"] == raw
    assert (
        next(r for r in generated if r["panel"] == "free")["first_valid_utf8"] is False
    )
