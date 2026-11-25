"""Genuine frozen-initialization roll-ins; no production bank before warm-up.

The pilot uses token-wise grammar masking, explicitly not free authorship.
Evaluation is unconstrained and retains non-events/parse failures.
"""

from __future__ import annotations

import time
from pathlib import Path

import torch
from torch.nn import functional as F

from ..models import ModelConfig, build_model
from ..q3a.io import read_json, read_rows, sha256, signature, write_json, write_rows
from ..q3a.plan import load_plan as load_initialization_plan
from ..tokenizer import ByteTokenizer
from .data import c_suffix, history_options, parse_controlled_history, verify

T = ByteTokenizer()


def load_initialization(plan, root, kind, seed, device):
    path = Path(root) / f"warmup-{kind}-s{seed}" / "final.pt"
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    expected = next(r for r in plan["runs"] if r["id"] == f"warmup-{kind}-s{seed}")
    if (
        checkpoint["plan_id"] != plan["plan_id"]
        or checkpoint["run"] != expected
        or not checkpoint["complete"]
    ):
        raise ValueError(
            "A complete checkpoint from the shared warm-up plan is required"
        )
    if checkpoint["stats"]["trained_targets"] != expected["targets"]:
        raise ValueError("Warm-up target budget incomplete")
    model = build_model(ModelConfig(**checkpoint["config"])).to(device)
    model.load_state_dict(checkpoint["model"])
    model.eval()
    return model, sha256(path)


@torch.inference_mode()
def constrained_history(model, row, *, seed, device="cpu"):
    candidates = [T.encode(x["text"], eos=True) for x in history_options(row)]
    prefix = T.encode(row["prompt"], bos=True)
    logits, _, state = model(torch.tensor([prefix], device=device), return_state=True)
    rng = torch.Generator(device=device).manual_seed(seed)
    emitted = []
    for _ in range(max(map(len, candidates))):
        allowed = sorted(
            {c[len(emitted)] for c in candidates if c[: len(emitted)] == emitted}
        )
        if not allowed:
            raise ValueError("Grammar has no continuation")
        ids = torch.tensor(allowed, device=device)
        scores = logits[0, -1, ids].float()
        index = int(torch.multinomial(torch.softmax(scores, 0), 1, generator=rng))
        token = allowed[index]
        if token == T.eos_id:
            break
        emitted.append(token)
        logits, _, state = model(
            torch.tensor([[token]], device=device), state=state, return_state=True
        )
    text = T.decode(emitted)
    parsed = parse_controlled_history(row, text)
    if parsed is None:
        raise ValueError("Decoder did not complete a sound controlled history")
    return {
        "text": text,
        "token_ids": emitted,
        "place": parsed["place"],
        "style": parsed["style"],
        "constrained": True,
        "grammar_sha256": signature(history_options(row)),
        "generation_seed": seed,
    }


@torch.inference_mode()
def history_surprisal(model, row, history, *, device="cpu"):
    prefix = T.encode(row["prompt"], bos=True)
    suffix = history["token_ids"] + [T.eos_id]
    ids = prefix + suffix
    inputs = torch.tensor([ids[:-1]], device=device)
    labels = torch.tensor(suffix, device=device)
    logits, _ = model(inputs)
    return float(F.cross_entropy(logits[0, len(prefix) - 1 :], labels))


def collect(
    shared_plan, data_dir, warmup_root, output, *, source_limit=24, device="cpu"
):
    plan = load_initialization_plan(shared_plan)
    m = verify(data_dir)
    if m["study"] != "c":
        raise ValueError("C data required")
    rows = read_rows(Path(data_dir) / "train.jsonl")[:source_limit]
    if not rows or source_limit < 1:
        raise ValueError("Positive candidate-source cap required")
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    hashes = {}
    checkpoints = {}
    started = time.perf_counter()
    tokens = 0
    for kind in plan["config"]["backbones"]:
        for seed in plan["config"]["seeds"]:
            model, digest = load_initialization(plan, warmup_root, kind, seed, device)
            checkpoints[f"{kind}/s{seed}"] = digest
            histories = []
            for i, row in enumerate(rows):
                history = constrained_history(
                    model, row, seed=100000 * seed + i + 2026, device=device
                )
                histories.append(
                    {
                        "source_id": row["source_id"],
                        "origin": "frozen_model_constrained",
                        "kind": kind,
                        "seed": seed,
                        "checkpoint_sha256": digest,
                        "prompt_sha256": signature(row["prompt"]),
                        **history,
                    }
                )
                tokens += len(history["token_ids"])
            path = output / f"{kind}-s{seed}.jsonl"
            write_rows(path, histories)
            hashes[path.name] = sha256(path)
    manifest = {
        "shared_plan_id": plan["plan_id"],
        "dataset_id": m["dataset_id"],
        "source_limit": len(rows),
        "checkpoint_sha256": checkpoints,
        "sha256": hashes,
        "generated_tokens": tokens,
        "elapsed_seconds": time.perf_counter() - started,
        "mode": "token-wise grammar-constrained frozen-model histories",
        "human_labels": False,
        "free_authorship_claim": False,
    }
    manifest["bank_id"] = signature(manifest)
    write_json(output / "manifest.json", manifest)
    return manifest


def verify_bank(directory):
    directory = Path(directory)
    m = read_json(directory / "manifest.json")
    check = dict(m)
    identity = check.pop("bank_id")
    if signature(check) != identity:
        raise ValueError("Bank manifest modified")
    for name, digest in m["sha256"].items():
        if sha256(directory / name) != digest:
            raise ValueError("Raw history bank modified")
    return m


def seal(
    shared_plan,
    data_dir,
    warmup_root,
    bank_dir,
    output,
    *,
    minimum_sources=30,
    max_nll_gap=0.25,
    max_length_gap=32,
    device="cpu",
):
    plan = load_initialization_plan(shared_plan)
    data = verify(data_dir)
    bank = verify_bank(bank_dir)
    if (
        bank["shared_plan_id"] != plan["plan_id"]
        or bank["dataset_id"] != data["dataset_id"]
    ):
        raise ValueError("Wrong initialization/data provenance")
    if minimum_sources < 1 or max_nll_gap < 0 or max_length_gap < 0:
        raise ValueError("Invalid preregistered matching limits")
    rows = {r["source_id"]: r for r in read_rows(Path(data_dir) / "train.jsonl")}
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    summaries = []
    files = {}
    started = time.perf_counter()
    for kind in plan["config"]["backbones"]:
        raw = {
            s: {
                r["source_id"]: r
                for r in read_rows(Path(bank_dir) / f"{kind}-s{s}.jsonl")
            }
            for s in plan["config"]["seeds"]
        }
        for seed in plan["config"]["seeds"]:
            model, digest = load_initialization(plan, warmup_root, kind, seed, device)
            peer = (seed + 1) % 3
            if bank["checkpoint_sha256"][f"{kind}/s{seed}"] != digest:
                raise ValueError("Learner initialization changed")
            selected = {arm: [] for arm in ("C0", "C1", "C2", "C3")}
            stats = {
                "offered": 0,
                "event_mismatch": 0,
                "caliper_rejected": 0,
                "same_text": 0,
                "matched": 0,
            }
            for source in sorted(set(raw[seed]) & set(raw[peer])):
                row = rows[source]
                own = raw[seed][source]
                other = raw[peer][source]
                stats["offered"] += 1
                for h, expected_seed in ((own, seed), (other, peer)):
                    if h["kind"] != kind or h["seed"] != expected_seed:
                        raise ValueError(
                            "Self/peer actor identity differs from its bank file"
                        )
                    if (
                        T.decode(h["token_ids"]) != h["text"]
                        or parse_controlled_history(row, h["text"]) is None
                    ):
                        raise ValueError("Unverified controlled history")
                    parsed = parse_controlled_history(row, h["text"])
                    if (
                        parsed["place"] != h["place"]
                        or parsed["style"] != h["style"]
                        or h["prompt_sha256"] != signature(row["prompt"])
                    ):
                        raise ValueError("History event or prompt annotation changed")
                    if (
                        h["checkpoint_sha256"]
                        != bank["checkpoint_sha256"][f"{kind}/s{h['seed']}"]
                    ):
                        raise ValueError("History checkpoint provenance changed")
                if own["place"] != other["place"]:
                    stats["event_mismatch"] += 1
                    continue
                nll_self = history_surprisal(model, row, own, device=device)
                nll_peer = history_surprisal(model, row, other, device=device)
                if (
                    abs(nll_self - nll_peer) > max_nll_gap
                    or abs(len(own["token_ids"]) - len(other["token_ids"]))
                    > max_length_gap
                ):
                    stats["caliper_rejected"] += 1
                    continue
                place = own["place"]
                teacher = next(
                    h
                    for h in history_options(row)
                    if h["place"] == place and h["style"] == row["teacher_style"]
                )
                chosen = {
                    "C0": teacher,
                    "C1": other,
                    "C2": own,
                    "C3": teacher if stats["matched"] % 2 == 0 else own,
                }
                for arm, history in chosen.items():
                    selected[arm].append(
                        {
                            "source_id": source,
                            "split": "train",
                            "prompt": row["prompt"] + history["text"] + row["followup"],
                            "reference": c_suffix(row, place),
                            "history_text": history["text"],
                            "history_token_ids": history.get(
                                "token_ids", T.encode(history["text"])
                            ),
                            "place": place,
                            "origin_arm": arm,
                            "frozen_learner_sha256": digest,
                            "self_surprisal": nll_self,
                            "peer_surprisal": nll_peer,
                            "peer_seed": peer,
                            "controlled_grammar_verified": True,
                        }
                    )
                stats["matched"] += 1
                stats["same_text"] += int(own["text"] == other["text"])
            stats.update(
                kind=kind, seed=seed, peer_seed=peer, minimum_sources=minimum_sources
            )
            summaries.append(stats)
            stats["distinct_history_sources"] = stats["matched"] - stats["same_text"]
            if (
                stats["matched"] < minimum_sources
                or stats["distinct_history_sources"] == 0
            ):
                continue
            for arm, examples in selected.items():
                path = output / f"{arm}-{kind}-s{seed}.jsonl"
                write_rows(path, examples)
                files[path.name] = sha256(path)
    ready = len(files) == 24
    manifest = {
        "shared_plan_id": plan["plan_id"],
        "dataset_id": data["dataset_id"],
        "raw_bank_id": bank["bank_id"],
        "sha256": files,
        "matching": summaries,
        "ready": ready,
        "minimum_sources": minimum_sources,
        "max_nll_gap": max_nll_gap,
        "max_length_gap": max_length_gap,
        "elapsed_seconds": time.perf_counter() - started,
        "claim_scope": "controlled roll-in distribution effect, not intrinsic origin identity or free-authored quality",
        "status": "sealed" if ready else "insufficient_overlap_stop_without_training",
    }
    manifest["sealed_bank_id"] = signature(manifest)
    write_json(output / "manifest.json", manifest)
    return manifest
