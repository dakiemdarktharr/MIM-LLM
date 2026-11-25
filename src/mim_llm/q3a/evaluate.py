"""Free generation, blank blinded annotation, and source-paired analysis.

No automatic free-text oracle is presented as a human-validated primary metric.
"""

from __future__ import annotations

import csv
import random
import statistics
from collections import defaultdict
from pathlib import Path

import torch

from ..generate import generate
from ..models import ModelConfig, build_model
from .io import read_json, read_rows, sha256, signature, write_rows
from .plan import load_plan
from .runner import language_examples, validation_loss


def load_q3a_checkpoint(path, plan, device):
    ckpt = torch.load(path, map_location="cpu", weights_only=True)
    if ckpt["plan_id"] != plan["plan_id"]:
        raise ValueError("Checkpoint from different plan")
    model = build_model(ModelConfig(**ckpt["config"])).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()
    return model, ckpt


def check_test_release(plan, checkpoint, selection):
    if selection is None:
        raise ValueError("Test is locked until validation selection is frozen")
    lock = read_json(selection)
    if (
        not lock.get("selection_frozen")
        or lock["plan_id"] != plan["plan_id"]
        or lock["dataset_id"] != plan["dataset_id"]
    ):
        raise ValueError("Invalid selection freeze")
    if lock["decoding"] != plan["config"]["decoding"]:
        raise ValueError("Decoding differs from frozen selection")
    if sha256(checkpoint) not in lock["checkpoints"].values():
        raise ValueError("Checkpoint not frozen")


def generate_panel(
    plan_path, checkpoint, output, *, split="validation", device="cpu", selection=None
):
    plan = load_plan(plan_path)
    if split not in ("validation", "test"):
        raise ValueError("Only validation/test panels")
    if split == "test":
        check_test_release(plan, checkpoint, selection)
    from ..tokenizer import ByteTokenizer

    model, ckpt = load_q3a_checkpoint(checkpoint, plan, device)
    if ckpt["run"]["phase"] != "post":
        raise ValueError("Use a post-training checkpoint")
    if not ckpt["complete"]:
        raise ValueError("Run must complete its declared target budget")
    decoding = plan["config"]["decoding"]
    rows = []
    digest = sha256(checkpoint)
    selected = (
        set(read_json(selection)["analysis_registration"]["test_source_ids"])
        if split == "test"
        else None
    )
    for b in read_rows(Path(plan["data_dir"]) / f"{split}.jsonl"):
        if selected is not None and b["source_id"] not in selected:
            continue
        for role in ("base", "effective", "noop"):
            s = b["scenarios"][role]
            for seed in decoding["seeds"]:
                output_row = {
                    "source_id": b["source_id"],
                    "scenario_id": s["id"],
                    "role": role,
                    "split": split,
                    "world": s["world"],
                    "expected_facts": s["facts"],
                    "mandatory": s["mandatory"],
                    "pairs": b["pairs"],
                    "run": ckpt["run"],
                    "plan_id": plan["plan_id"],
                    "checkpoint_sha256": digest,
                    "decode_seed": seed,
                }
                output_row["generation_id"] = signature(
                    {
                        k: output_row[k]
                        for k in (
                            "scenario_id",
                            "run",
                            "checkpoint_sha256",
                            "decode_seed",
                        )
                    }
                )
                sample = generate(
                    model,
                    ByteTokenizer(),
                    s["prompt"],
                    max_new_tokens=decoding["max_new_tokens"],
                    temperature=decoding["temperature"],
                    top_k=decoding["top_k"],
                    seed=seed,
                    device=device,
                )
                rows.append({**output_row, **sample})
    write_rows(output, rows)
    return {
        "generations": len(rows),
        "split": split,
        "human_labels": False,
        "output_sha256": sha256(output),
    }


FIELDS = [
    "item_id",
    "rater_id",
    "all_mandatory_correct",
    "holder_correct",
    "action_correct",
    "cabinet_correct",
    "reason_correct",
    "contradiction",
    "contradiction_type",
    "format_3_to_5",
    "coverage_fraction",
    "fluency_1_to_5",
    "unclear",
    "evidence",
]


def blind_packet(generation_files, output, *, seed=2026):
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    rows = [r for p in generation_files for r in read_rows(p)]
    if not rows or len({r["generation_id"] for r in rows}) != len(rows):
        raise ValueError("Empty/duplicate generations")
    random.Random(seed).shuffle(rows)
    output.mkdir(parents=True)
    public = []
    key = []
    for i, r in enumerate(rows):
        item = f"item-{i:07d}"
        public.append(
            {
                "item_id": item,
                "prompt": r["prompt"],
                "continuation": r["continuation"],
                "required_propositions": r["mandatory"],
                "applicable_facts_for_contradiction_checks": r["expected_facts"],
                "decision_time_minutes": r["world"]["deadline"],
            }
        )
        key.append(
            {
                "item_id": item,
                **{
                    k: r[k]
                    for k in (
                        "generation_id",
                        "source_id",
                        "role",
                        "run",
                        "decode_seed",
                        "pairs",
                        "split",
                        "plan_id",
                    )
                },
            }
        )
    write_rows(output / "packet.jsonl", public)
    write_rows(output / "PRIVATE-key.jsonl", key)
    for reader in ("reader-a", "reader-b"):
        with (output / f"{reader}.csv").open("x", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            for p in public:
                writer.writerow({"item_id": p["item_id"]})
    return {
        "items": len(public),
        "labels_prefilled": False,
        "key_must_be_hidden_from_readers": True,
    }


def read_labels(path, items):
    with Path(path).open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != len(items) or {r["item_id"] for r in rows} != items:
        raise ValueError("Missing/duplicate/extra annotations")
    result = {}
    for r in rows:
        if not r["rater_id"].strip():
            raise ValueError("Real rater ID required")
        for field in (
            "all_mandatory_correct",
            "holder_correct",
            "action_correct",
            "cabinet_correct",
            "reason_correct",
            "contradiction",
            "format_3_to_5",
            "unclear",
        ):
            if r[field] not in ("0", "1"):
                raise ValueError("Blank/invalid labels are not results")
            r[field] = int(r[field])
        if r["all_mandatory_correct"] != int(
            all(
                r[f"{name}_correct"]
                for name in ("holder", "action", "cabinet", "reason")
            )
        ):
            raise ValueError("Joint correctness must agree with proposition labels")
        if not r["evidence"].strip():
            raise ValueError("Evidence/unclear reason required")
        types = {
            "none",
            "holder",
            "temporal",
            "conditional",
            "cross-world",
            "self-generated",
            "multiple",
            "other",
        }
        if r["contradiction_type"] not in types or (
            (r["contradiction_type"] == "none") != (r["contradiction"] == 0)
        ):
            raise ValueError("Contradiction type must agree with its indicator")
        coverage = float(r["coverage_fraction"])
        fluency = int(r["fluency_1_to_5"])
        if not 0 <= coverage <= 1 or not 1 <= fluency <= 5:
            raise ValueError("Invalid coverage/fluency")
        r["coverage_fraction"] = coverage
        r["fluency_1_to_5"] = fluency
        result[r["item_id"]] = r
    return result


def paired_bootstrap(values, *, draws=2000, seed=2026):
    if not values or draws < 100:
        raise ValueError("Need nonempty clusters and >=100 draws")
    rng = random.Random(seed)
    n = len(values)
    samples = sorted(statistics.mean(rng.choices(values, k=n)) for _ in range(draws))
    return {
        "effect": statistics.mean(values),
        "ci95": [samples[int(0.025 * (draws - 1))], samples[int(0.975 * (draws - 1))]],
        "source_clusters": n,
        "interval_scope": "source resampling conditional on observed training seeds",
    }


def analyze(labels_a, labels_b, key_path, *, adjudicated=None, draws=2000):
    key = read_rows(key_path)
    if len({r["plan_id"] for r in key}) != 1 or len({r["split"] for r in key}) != 1:
        raise ValueError("Do not mix plans or validation/test labels")
    items = {r["item_id"] for r in key}
    if len(items) != len(key):
        raise ValueError("Duplicate key")
    a = read_labels(labels_a, items)
    b = read_labels(labels_b, items)
    if {r["rater_id"] for r in a.values()} & {r["rater_id"] for r in b.values()}:
        raise ValueError("Independent rater IDs required")
    fields = (
        "all_mandatory_correct",
        "holder_correct",
        "action_correct",
        "cabinet_correct",
        "reason_correct",
        "contradiction",
        "contradiction_type",
        "format_3_to_5",
        "unclear",
    )
    disagreements = [i for i in items if any(a[i][f] != b[i][f] for f in fields)]
    agreement = 1 - len(disagreements) / len(items)
    sa = [
        int(
            a[i]["all_mandatory_correct"]
            and a[i]["format_3_to_5"]
            and not a[i]["contradiction"]
            and not a[i]["unclear"]
        )
        for i in sorted(items)
    ]
    sb = [
        int(
            b[i]["all_mandatory_correct"]
            and b[i]["format_3_to_5"]
            and not b[i]["contradiction"]
            and not b[i]["unclear"]
        )
        for i in sorted(items)
    ]
    observed = sum(x == y for x, y in zip(sa, sb)) / len(sa)
    pa = statistics.mean(sa)
    pb = statistics.mean(sb)
    chance = pa * pb + (1 - pa) * (1 - pb)
    kappa = (observed - chance) / (1 - chance) if chance < 1 else None
    if disagreements and adjudicated is None:
        return {
            "adjudication_required": True,
            "disagreement_items": sorted(disagreements),
            "raw_joint_agreement": agreement,
            "success_kappa": kappa,
            "primary_results": None,
        }
    labels = read_labels(adjudicated, items) if adjudicated else a
    grouped = defaultdict(dict)
    pair_definitions = {}
    quality = defaultdict(list)
    for r in key:
        lab = labels[r["item_id"]]
        run = r["run"]
        k = (run["kind"], run["arm"], run["seed"], r["decode_seed"], r["source_id"])
        pair_definitions[k] = {p["kind"]: p for p in r["pairs"]}
        if r["role"] in grouped[k]:
            raise ValueError("Duplicate scenario/run/seed annotation")
        grouped[k][r["role"]] = lab
        quality[(run["kind"], run["arm"], run["seed"])].append(lab)
    source_scores = defaultdict(dict)
    unclear = 0
    strata = defaultdict(list)
    predicate_scores = defaultdict(lambda: {"changed": [], "preserved": []})
    for (kind, arm, train_seed, decode_seed, source), roles in grouped.items():
        if set(roles) != {"base", "effective", "noop"}:
            raise ValueError("Incomplete scenario panel")

        def success(r):
            return int(
                r["all_mandatory_correct"]
                and r["format_3_to_5"]
                and not r["contradiction"]
                and not r["unclear"]
            )

        unclear += sum(r["unclear"] for r in roles.values())
        scores = {
            p: success(roles["base"]) * success(roles[p]) for p in ("effective", "noop")
        }
        source_scores[(kind, arm, train_seed, decode_seed)][source] = statistics.mean(
            scores.values()
        )
        for pair_kind, y in scores.items():
            strata[(kind, arm, train_seed, pair_kind)].append(y)
            definitions = pair_definitions[(kind, arm, train_seed, decode_seed, source)]
            if set(definitions) != {"effective", "noop"}:
                raise ValueError("Missing pair definitions")
            for category in ("changed", "preserved"):
                for field in definitions[pair_kind][category]:
                    if field not in ("holder", "action", "cabinet"):
                        continue
                    value = (
                        roles["base"][field + "_correct"]
                        * roles[pair_kind][field + "_correct"]
                    )
                    predicate_scores[(kind, arm, train_seed, pair_kind)][
                        category
                    ].append(value)
    contrasts = []
    for kind in sorted({k[0] for k in source_scores}):
        per_source = defaultdict(list)
        per_seed = []
        left = {k[2:] for k in source_scores if k[:2] == (kind, "A1")}
        right = {k[2:] for k in source_scores if k[:2] == (kind, "A2")}
        if left != right or not left:
            raise ValueError("Primary conditions have unequal/missing seeds")
        for train_seed, decode_seed in sorted(left):
            aa = source_scores[(kind, "A1", train_seed, decode_seed)]
            bb = source_scores[(kind, "A2", train_seed, decode_seed)]
            if set(aa) != set(bb):
                raise ValueError("Unpaired sources")
            diffs = {s: aa[s] - bb[s] for s in aa}
            for s, d in diffs.items():
                per_source[s].append(d)
            per_seed.append(
                {
                    "training_seed": train_seed,
                    "decoding_seed": decode_seed,
                    "difference": statistics.mean(diffs.values()),
                }
            )
        contrasts.append(
            {
                "backbone": kind,
                "contrast": "A1 minus A2",
                "per_seed": per_seed,
                **paired_bootstrap(
                    [statistics.mean(v) for v in per_source.values()], draws=draws
                ),
            }
        )
    return {
        "primary_results": contrasts,
        "raw_joint_agreement": agreement,
        "success_kappa": kappa,
        "split": key[0]["split"],
        "all_three_training_seeds_present": all(
            {r["training_seed"] for r in c["per_seed"]} == {0, 1, 2} for c in contrasts
        ),
        "quality_summaries": [
            {
                "backbone": k[0],
                "arm": k[1],
                "training_seed": k[2],
                "coverage": statistics.mean(r["coverage_fraction"] for r in v),
                "fluency": statistics.mean(r["fluency_1_to_5"] for r in v),
                "contradiction_rate": statistics.mean(r["contradiction"] for r in v),
                "contradiction_types": {
                    t: sum(r["contradiction_type"] == t for r in v)
                    for t in sorted({r["contradiction_type"] for r in v})
                },
            }
            for k, v in sorted(quality.items())
        ],
        "unclear_retained_as_failures": unclear,
        "stratified_pair_success": [
            {
                "backbone": k[0],
                "arm": k[1],
                "training_seed": k[2],
                "pair_kind": k[3],
                "success_rate": statistics.mean(v),
                "changed_proposition_accuracy": statistics.mean(
                    predicate_scores[k]["changed"]
                )
                if predicate_scores[k]["changed"]
                else None,
                "preserved_proposition_accuracy": statistics.mean(
                    predicate_scores[k]["preserved"]
                )
                if predicate_scores[k]["preserved"]
                else None,
            }
            for k, v in sorted(strata.items())
        ],
        "training_seed_uncertainty": "Report individual seeds; source CI is not an across-training-seed guarantee",
        "label_files_sha256": [sha256(labels_a), sha256(labels_b)],
        "key_sha256": sha256(key_path),
    }


def perplexity(plan_path, checkpoint, *, split="validation", device="cpu"):
    if split != "validation":
        raise ValueError(
            "General-text test use requires separate preregistered release"
        )
    plan = load_plan(plan_path)
    model, _ = load_q3a_checkpoint(checkpoint, plan, device)
    examples = language_examples(
        read_rows(plan["warmup"]), split, plan["config"]["context"]
    )
    return validation_loss(
        model, examples, plan["config"]["context"], plan["config"]["batch_size"], device
    )
