"""Unconstrained continuation, raw self-history preservation and blind labels."""

from __future__ import annotations

import random
import statistics
from collections import defaultdict
from pathlib import Path

import torch

from ..generate import generate, generate_from_ids
from ..models import ModelConfig, build_model
from ..q3a.evaluate import paired_bootstrap
from ..q3a.io import read_json, read_rows, sha256, signature, write_json, write_rows
from ..tokenizer import ByteTokenizer
from .data import b_probe, history_options
from .plan import load_plan

T = ByteTokenizer()


def perplexity(
    plan_path, checkpoint, *, split="validation", selection=None, device="cpu"
):
    from ..q3a.plan import load_plan as load_shared
    from ..q3a.runner import language_examples, validation_loss
    from ..shared_data import general_rows

    p = load_plan(plan_path, require_bank=True)
    if split not in ("validation", "test"):
        raise ValueError("Held-out split required")
    if split == "test":
        test_sources(p, checkpoint, selection)
    shared = load_shared(p["shared_plan"])
    model, _ = load_model(p, checkpoint, device)
    examples = language_examples(
        general_rows(shared["warmup"]), split, p["config"]["context"]
    )
    result = validation_loss(
        model, examples, p["config"]["context"], p["config"]["batch_size"], device
    )
    return {
        "split": split,
        "corpus": "original held-out TinyStories, excluding derived instruction examples",
        **result,
    }


def load_model(plan, checkpoint, device):
    ckpt = torch.load(checkpoint, map_location="cpu", weights_only=True)
    if ckpt["plan_id"] != plan["plan_id"] or not ckpt["complete"]:
        raise ValueError("Complete checkpoint from this plan required")
    model = build_model(ModelConfig(**ckpt["config"])).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()
    return model, ckpt


def test_sources(plan, checkpoint, selection):
    if selection is None:
        raise ValueError("Test locked: freeze selection/registration first")
    lock = read_json(selection)
    if (
        not lock.get("selection_frozen")
        or lock["plan_id"] != plan["plan_id"]
        or lock["decoding"] != plan["config"]["decoding"]
    ):
        raise ValueError("Wrong selection/decoding")
    if sha256(checkpoint) not in lock["checkpoints"].values():
        raise ValueError("Checkpoint hash not frozen")
    return set(lock["registration"]["test_source_ids"])


def generate_panel(
    plan_path, checkpoint, output, *, split="validation", selection=None, device="cpu"
):
    p = load_plan(plan_path, require_bank=True)
    if split not in ("validation", "test"):
        raise ValueError("Only held-out panels")
    sources = test_sources(p, checkpoint, selection) if split == "test" else None
    model, ckpt = load_model(p, checkpoint, device)
    d = p["config"]["decoding"]
    out = []
    for row in read_rows(Path(p["data_dir"]) / f"{split}.jsonl"):
        if sources is not None and row["source_id"] not in sources:
            continue
        for seed in d["seeds"]:
            base = {
                "study": p["study"],
                "plan_id": p["plan_id"],
                "source_id": row["source_id"],
                "split": split,
                "run": ckpt["run"],
                "decode_seed": seed,
                "checkpoint_sha256": sha256(checkpoint),
            }
            if p["study"] == "b":
                sample = generate(
                    model,
                    T,
                    row["prompt"],
                    max_new_tokens=d["max_new_tokens"],
                    temperature=d["temperature"],
                    top_k=d["top_k"],
                    seed=seed,
                    device=device,
                )
                out.append(
                    {
                        **base,
                        **sample,
                        "panel": "continuation",
                        "mandatory": row["mandatory"],
                        "first_segment": None,
                        "lag": row["lag"],
                        "writes": row["writes"],
                    }
                )
            else:
                first = generate(
                    model,
                    T,
                    row["prompt"],
                    max_new_tokens=d["first_tokens"],
                    temperature=d["temperature"],
                    top_k=d["top_k"],
                    seed=seed,
                    device=device,
                )
                common = next(
                    x
                    for x in history_options(row)
                    if x["place"] == row["teacher_place"]
                    and x["style"] == row["teacher_style"]
                )
                for panel, text, ids in [
                    ("free", first["continuation"], first["token_ids"]),
                    ("fixed", common["text"], T.encode(common["text"])),
                ]:
                    # Preserve raw generated IDs; never replace the model's choice with teacher intent.
                    history_ids = (
                        T.encode(row["prompt"], bos=True)
                        + ids
                        + T.encode(row["followup"])
                    )
                    second = generate_from_ids(
                        model,
                        T,
                        history_ids,
                        max_new_tokens=d["max_new_tokens"],
                        temperature=d["temperature"],
                        top_k=d["top_k"],
                        seed=seed + 1000,
                        device=device,
                    )
                    out.append(
                        {
                            **base,
                            "panel": panel,
                            "prompt": row["prompt"],
                            "first_segment": text,
                            "first_token_ids": ids,
                            "first_valid_utf8": first["valid_utf8"]
                            if panel == "free"
                            else True,
                            "followup_prompt": row["followup"],
                            "frozen_history_ids_sha256": signature(history_ids),
                            "frozen_history_token_ids": history_ids,
                            **second,
                            "mandatory": {
                                "actual_event_followup": "follow the event actually written in first segment",
                                "valid_explanation": "do not invent an intervening move or revert to an earlier state",
                            },
                        }
                    )
    for row in out:
        row["generation_id"] = signature(
            {
                k: row[k]
                for k in (
                    "plan_id",
                    "run",
                    "source_id",
                    "decode_seed",
                    "panel",
                    "checkpoint_sha256",
                )
            }
        )
    write_rows(output, out)
    return {
        "records": len(out),
        "unconstrained_generation": True,
        "human_labels": False,
        "sha256": sha256(output),
    }


def probe_evaluate(plan_path, checkpoint, output, *, device="cpu"):
    p = load_plan(plan_path)
    if p["study"] != "b":
        raise ValueError("Only B has component probes")
    model, ckpt = load_model(p, checkpoint, device)
    rows = []
    for i, r in enumerate(read_rows(Path(p["data_dir"]) / "validation.jsonl")):
        probe = b_probe(r, ckpt["run"]["arm"], i)
        s = generate(
            model,
            T,
            probe["prompt"],
            max_new_tokens=16,
            temperature=0.8,
            top_k=40,
            seed=17,
            device=device,
        )
        rows.append(
            {
                "source_id": r["source_id"],
                "expected": probe["reference"],
                "answer": s["continuation"],
                "exact_match": s["continuation"].strip() == probe["reference"],
                "component_only": True,
            }
        )
    write_rows(output, rows)
    return {
        "probe_accuracy": statistics.mean(r["exact_match"] for r in rows),
        "not_primary_generator_metric": True,
    }


def blind_packet(paths, output, *, seed=2026):
    rows = [r for path in paths for r in read_rows(path)]
    output = Path(output)
    if not rows or len({r["generation_id"] for r in rows}) != len(rows):
        raise ValueError("Empty/duplicate generations")
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    random.Random(seed).shuffle(rows)
    packet = []
    key = []
    labels = []
    for i, r in enumerate(rows):
        item = f"item-{i:07d}"
        packet.append(
            {
                "item_id": item,
                "prompt": r["prompt"],
                "first_segment": r["first_segment"],
                "followup_prompt": r.get("followup_prompt"),
                "continuation": r["continuation"],
                "mandatory": r["mandatory"],
            }
        )
        key.append(
            {
                "item_id": item,
                **{
                    k: r[k]
                    for k in (
                        "study",
                        "plan_id",
                        "source_id",
                        "split",
                        "run",
                        "decode_seed",
                        "panel",
                        "generation_id",
                    )
                },
            }
        )
        key[-1].update(
            text_valid=bool(
                r.get("valid_utf8", True) and r.get("first_valid_utf8", True)
            ),
            lag=r.get("lag"),
            writes=r.get("writes"),
        )
        labels.append(
            {
                "item_id": item,
                "rater_id": "",
                "propositions": {k: None for k in r["mandatory"]},
                "instructions_met": None,
                "contradiction": None,
                "contradiction_type": None,
                "format_3_to_5": None,
                "new_event": None,
                "prefix_valid": None,
                "followup_consistent": None,
                "unclear": None,
                "coverage_fraction": None,
                "fluency_1_to_5": None,
                "evidence": "",
            }
        )
    write_rows(output / "packet.jsonl", packet)
    write_rows(output / "PRIVATE-key.jsonl", key)
    write_rows(output / "reader-a.jsonl", labels)
    write_rows(output / "reader-b.jsonl", labels)
    return {
        "items": len(packet),
        "labels_prefilled": False,
        "keep_private_key_from_readers": True,
    }


def read_labels(path, key):
    rows = read_rows(path)
    items = {r["item_id"] for r in key}
    if len(rows) != len(items) or {r["item_id"] for r in rows} != items:
        raise ValueError("Missing/duplicate/extra labels")
    study = key[0]["study"]
    result = {}
    for r in rows:
        if not r["rater_id"].strip() or not r["evidence"].strip():
            raise ValueError("Real reader ID and evidence required")
        binary = ["instructions_met", "contradiction", "format_3_to_5", "unclear"] + (
            ["new_event", "prefix_valid", "followup_consistent"] if study == "c" else []
        )
        if any(type(r[k]) is not int or r[k] not in (0, 1) for k in binary):
            raise ValueError("Blank/invalid binary judgments")
        if not r["propositions"] or any(
            type(v) is not int or v not in (0, 1) for v in r["propositions"].values()
        ):
            raise ValueError("Blank proposition labels")
        expected = (
            {"location", "latest_update", "retention"}
            if study == "b"
            else {"actual_event_followup", "valid_explanation"}
        )
        if set(r["propositions"]) != expected:
            raise ValueError("Wrong proposition schema")
        types = {
            "none",
            "location",
            "temporal",
            "revision",
            "self-event",
            "cross-world",
            "multiple",
            "other",
        }
        if r["contradiction_type"] not in types or (
            (r["contradiction_type"] == "none") != (r["contradiction"] == 0)
        ):
            raise ValueError("Invalid contradiction type")
        if (
            not isinstance(r["coverage_fraction"], (int, float))
            or not 0 <= r["coverage_fraction"] <= 1
            or r["fluency_1_to_5"] not in (1, 2, 3, 4, 5)
        ):
            raise ValueError("Invalid quality scores")
        result[r["item_id"]] = r
    return result


def analyze(labels_a, labels_b, key_path, output, *, adjudicated=None, draws=2000):
    key = read_rows(key_path)
    for field in ("study", "plan_id", "split"):
        if len({r[field] for r in key}) != 1:
            raise ValueError("Do not mix studies/plans/splits")
    a = read_labels(labels_a, key)
    b = read_labels(labels_b, key)
    if {r["rater_id"] for r in a.values()} & {r["rater_id"] for r in b.values()}:
        raise ValueError("Independent readers required")
    logic = [
        "propositions",
        "instructions_met",
        "contradiction",
        "contradiction_type",
        "format_3_to_5",
        "unclear",
    ] + (
        ["new_event", "prefix_valid", "followup_consistent"]
        if key[0]["study"] == "c"
        else []
    )
    disagreement = [i for i in a if any(a[i][k] != b[i][k] for k in logic)]

    def reader_success(r):
        y = int(
            all(r["propositions"].values())
            and r["instructions_met"]
            and r["format_3_to_5"]
            and not r["contradiction"]
            and not r["unclear"]
        )
        return (
            y * r["new_event"] * r["prefix_valid"] * r["followup_consistent"]
            if key[0]["study"] == "c"
            else y
        )

    aa = [reader_success(a[i]) for i in sorted(a)]
    bb = [reader_success(b[i]) for i in sorted(b)]
    observed = sum(x == y for x, y in zip(aa, bb)) / len(aa)
    pa = statistics.mean(aa)
    pb = statistics.mean(bb)
    chance = pa * pb + (1 - pa) * (1 - pb)
    kappa = (observed - chance) / (1 - chance) if chance < 1 else None
    if disagreement and not adjudicated:
        result = {
            "primary_results": None,
            "adjudication_required": True,
            "disagreement_items": disagreement,
            "success_kappa": kappa,
        }
        write_json(output, result)
        return result
    labels = read_labels(adjudicated, key) if adjudicated else a
    scores = {}
    quality = defaultdict(list)
    bygrid = defaultdict(list)
    conditional = defaultdict(list)
    for r in key:
        lab = labels[r["item_id"]]
        run = r["run"]
        k = (
            run["kind"],
            run["arm"],
            run["seed"],
            r["decode_seed"],
            r["source_id"],
            r["panel"],
        )
        if k in scores:
            raise ValueError("Duplicate complete source output")
        success = int(
            all(lab["propositions"].values())
            and lab["instructions_met"]
            and lab["format_3_to_5"]
            and not lab["contradiction"]
            and not lab["unclear"]
        )
        if r["study"] == "c":
            success *= (
                lab["new_event"] * lab["prefix_valid"] * lab["followup_consistent"]
            )
            if lab["new_event"] and lab["prefix_valid"]:
                conditional[(run["kind"], run["arm"], r["panel"])].append(
                    lab["followup_consistent"]
                )
        success *= int(r.get("text_valid", True))
        scores[k] = success
        if r["study"] == "b":
            bygrid[
                (run["kind"], run["arm"], run["seed"], r.get("lag"), r.get("writes"))
            ].append(success)
        quality_label = dict(lab)
        if not adjudicated:
            for field in ("coverage_fraction", "fluency_1_to_5"):
                quality_label[field] = statistics.mean(
                    (a[r["item_id"]][field], b[r["item_id"]][field])
                )
        quality[(run["kind"], run["arm"], run["seed"], r["panel"])].append(
            quality_label
        )
    study = key[0]["study"]
    left, right = ("B2", "B1") if study == "b" else ("C2", "C1")
    effects = []
    for kind in sorted({k[0] for k in scores}):
        for panel in sorted({k[-1] for k in scores if k[0] == kind}):
            lkeys = {k[2:5] for k in scores if k[:2] == (kind, left) and k[-1] == panel}
            rkeys = {
                k[2:5] for k in scores if k[:2] == (kind, right) and k[-1] == panel
            }
            if not lkeys or lkeys != rkeys:
                raise ValueError("Incomplete primary paired panel")
            expected = {(s, d) for s, d, _ in lkeys}
            for source in {x[2] for x in lkeys}:
                if {(s, d) for s, d, x in lkeys if x == source} != expected:
                    raise ValueError(
                        "Keep every observed seed/decoding in each source cluster"
                    )
            bysource = defaultdict(list)
            byseed = defaultdict(list)
            for train_seed, decode_seed, source in sorted(lkeys):
                diff = (
                    scores[(kind, left, train_seed, decode_seed, source, panel)]
                    - scores[(kind, right, train_seed, decode_seed, source, panel)]
                )
                bysource[source].append(diff)
                byseed[train_seed].append(diff)
            effects.append(
                {
                    "backbone": kind,
                    "panel": panel,
                    "primary": panel == ("continuation" if study == "b" else "free"),
                    "contrast": f"{left} minus {right}",
                    **paired_bootstrap(
                        [statistics.mean(v) for v in bysource.values()], draws=draws
                    ),
                    "per_seed": {str(s): statistics.mean(v) for s, v in byseed.items()},
                    "all_three_seeds": set(byseed) == {0, 1, 2},
                }
            )
    result = {
        "study": study,
        "split": key[0]["split"],
        "primary_results": effects,
        "raw_joint_agreement": 1 - len(disagreement) / len(key),
        "success_kappa": kappa,
        "lag_write_grid": [
            {
                "backbone": k[0],
                "arm": k[1],
                "seed": k[2],
                "lag": k[3],
                "writes": k[4],
                "source_count": len(v),
                "success": statistics.mean(v),
            }
            for k, v in bygrid.items()
        ],
        "quality": [
            {
                "backbone": k[0],
                "arm": k[1],
                "seed": k[2],
                "panel": k[3],
                "coverage": statistics.mean(x["coverage_fraction"] for x in v),
                "fluency": statistics.mean(x["fluency_1_to_5"] for x in v),
                "contradiction_rate": statistics.mean(x["contradiction"] for x in v),
                "contradiction_types": {
                    t: sum(x["contradiction_type"] == t for x in v)
                    for t in sorted({x["contradiction_type"] for x in v})
                },
                "unclear": sum(x["unclear"] for x in v),
                "event_creation_rate": statistics.mean(x["new_event"] for x in v)
                if study == "c"
                else None,
            }
            for k, v in sorted(quality.items())
        ],
        "conditional_followup": [
            {
                "backbone": k[0],
                "arm": k[1],
                "panel": k[2],
                "denominator": len(v),
                "consistency": statistics.mean(v),
            }
            for k, v in sorted(conditional.items())
        ],
        "interval_scope": "source clusters conditional on observed training seeds; report seed variability separately",
        "label_sha256": [sha256(labels_a), sha256(labels_b)],
        "key_sha256": sha256(key_path),
    }
    write_json(output, result)
    return result
