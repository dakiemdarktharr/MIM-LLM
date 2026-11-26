"""Controlled, source-disjoint counterfactual bundles (not human-authored data)."""

from __future__ import annotations

import itertools
import random
from functools import lru_cache
from pathlib import Path

from .io import (
    read_json,
    read_rows,
    sha256,
    signature,
    source_sha256,
    write_json,
    write_rows,
)

ROLES = ("base", "effective", "noop", "surface")
ARM_ROLES = {
    "A0": ("base", "effective", "base", "effective"),
    "A1": ("base", "effective", "base", "noop"),
    "A2": ("base", "effective", "base", "surface"),
    "A3": ("base", "effective", "base", "noop"),
}
NAMES = ("Lan", "Huy", "Mai", "An", "Binh", "Chi", "Dao", "Giang", "Linh", "Minh")


def clock(minutes):
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


@lru_cache(maxsize=8)
def nuisance_times(edit_count):
    return tuple(
        m
        for m in range(24 * 60 - 1)
        if sum(a != b for a, b in zip(clock(m), clock(m + 1))) == edit_count
    )


def state(world):
    holder = world["initial_holder"]
    for receiver in world["transfers"]:
        holder = receiver
    powered = world["power_return"] <= world["deadline"]
    opened = powered and world["permission"]
    return {
        "holder": holder,
        "power_available": powered,
        "permission": world["permission"],
        "action": "open" if opened else "wait",
        "cabinet": "open" if opened else "locked",
    }


def render(world, style, paraphrase=False):
    d = clock(world["deadline"])
    p = clock(world["power_return"])
    names = [world["initial_holder"], *world["transfers"]]
    starts = [
        f"The cabinet was locked. {names[0]} held its key.",
        f"{names[0]} had the key to a locked cabinet.",
        f"A locked cabinet stood in the room; its key was with {names[0]}.",
        f"The key for the cabinet, still locked, was held by {names[0]}.",
    ]
    parts = [starts[style]]
    for a, b in itertools.pairwise(names):
        parts.append(
            [
                f"{a} handed the key to {b}.",
                f"{a} passed the key to {b}.",
                f"The key moved from {a} to {b}.",
                f"{b} received the key from {a}.",
            ][style]
        )
    if world.get("attempted_receiver"):
        parts.append(
            f"{names[-1]} planned to hand the key to {world['attempted_receiver']}, but cancelled that plan; this transfer never happened."
        )
    parts.append(f"{world['distractor']} read a book nearby and never touched the key.")
    parts.append(
        f"An unrelated museum clock displayed {clock(world['background_clock'])}; its reading has no effect on this scene."
    )
    parts.append(
        f"Every completed handover occurred before {d}; cancelled plans were not executed. Everyone follows this one-time rule: at exactly {d}, the key holder must open the cabinet if power is available and permission has been granted; otherwise the holder must wait. The cabinet remains locked until that decision; no other opening occurs before it."
    )
    parts.append(
        "Permission had been granted."
        if world["permission"]
        else "Permission had not been granted."
    )
    parts.append(
        f"Electricity was restored at {p}." if paraphrase else f"Power returned at {p}."
    )
    parts.append(
        f"The given handovers, permission and power timeline are complete up to {d}. Describe that decision first, without adding earlier changes, then continue in three to five natural sentences. State who holds the key at the decision, what that person does then, whether the cabinet is open or locked then, and why. Additional coherent events are allowed after that decision."
    )
    return " ".join(parts) + "\nContinuation:\n"


def reference(world):
    s = state(world)
    h = s["holder"]
    d = clock(world["deadline"])
    first = f"At {d}, {h} held the key."
    if s["action"] == "open":
        return (
            first
            + f" {h} opened the cabinet at {d} because power was available and permission had been granted. The cabinet was open at that moment."
        )
    reason = (
        "power had not returned"
        if not s["power_available"]
        else "permission had not been granted"
    )
    return (
        first
        + f" {h} waited at {d} because {reason}. The cabinet was still locked at that moment."
    )


def make_bundle(source_id, split, seed, index):
    rng = random.Random(f"{seed}/{source_id}")
    deadline = rng.choice([8 * 60, 9 * 60, 10 * 60, 11 * 60])
    initial = rng.choice(NAMES)
    current = initial
    transfers = []
    for _ in range(1 + index % 6):
        current = rng.choice([n for n in NAMES if n != current])
        transfers.append(current)
    permission = index % 3 != 0
    early = (index % 2 == 0) or not permission
    arrival = deadline - rng.randint(4, 15) if early else deadline + rng.randint(4, 15)
    base = {
        "initial_holder": initial,
        "transfers": transfers,
        "distractor": rng.choice([n for n in NAMES if n != current]),
        "deadline": deadline,
        "power_return": arrival,
        "permission": permission,
    }
    base["attempted_receiver"] = (
        rng.choice([n for n in NAMES if n != current]) if index % 2 == 0 else None
    )
    edit_count = sum(a != b for a, b in zip(clock(arrival), clock(arrival + 1)))
    base["background_clock"] = rng.choice(nuisance_times(edit_count))
    effective = dict(base)
    if permission:
        effective["power_return"] = deadline + 5 if early else deadline - 5
        effective_field = "power_return"
    else:
        effective["permission"] = True
        effective_field = "permission"
    noop = dict(base)
    noop["power_return"] = arrival + 1
    surface = dict(base)
    surface["background_clock"] += 1
    style = {"train": index % 2, "validation": 2, "test": 3}[split]
    scenarios = {}
    for role, w in [
        ("base", base),
        ("effective", effective),
        ("noop", noop),
        ("surface", surface),
    ]:
        s = state(w)
        reason = (
            "power_and_permission"
            if s["action"] == "open"
            else (
                "power_unavailable"
                if not s["power_available"]
                else "permission_missing"
            )
        )
        scenarios[role] = {
            "id": f"{source_id}/{role}",
            "world": w,
            "prompt": render(w, style),
            "reference": reference(w),
            "facts": s,
            "mandatory": {
                "holder": s["holder"],
                "action": s["action"],
                "cabinet": s["cabinet"],
                "reason": reason,
            },
        }
        if role == "surface":
            a = scenarios["base"]["prompt"]
            b = scenarios["noop"]["prompt"]
            if len(a) != len(b):
                raise ValueError("Matched byte-length contract failed")
            edits = sum(x != y for x, y in zip(a, b))
            if edits != sum(x != y for x, y in zip(a, scenarios[role]["prompt"])):
                raise ValueError("Numeric nuisance control edit count mismatch")
            scenarios[role]["control_type"] = (
                "decision-irrelevant clock edit, numeric and byte/edit-count matched"
            )
            scenarios[role]["character_edits"] = edits
    pairs = []
    for kind in ("effective", "noop"):
        before = state(base)
        after = scenarios[kind]["facts"]
        pairs.append(
            {
                "pair_id": f"{source_id}/{kind}",
                "kind": kind,
                "roles": ["base", kind],
                "changed": [k for k in before if before[k] != after[k]],
                "preserved": [k for k in before if before[k] == after[k]],
                "intervention_field": effective_field
                if kind == "effective"
                else "power_return",
            }
        )
    result = {
        "source_id": source_id,
        "split": split,
        "origin": "project-controlled-template",
        "surface_family": style,
        "depth": len(transfers),
        "scenarios": scenarios,
        "pairs": pairs,
    }
    validate_bundle(result)
    return result


def validate_bundle(bundle):
    if set(bundle["scenarios"]) != set(ROLES):
        raise ValueError("Missing scenario roles")
    for scenario in bundle["scenarios"].values():
        if scenario["facts"] != state(scenario["world"]):
            raise ValueError("Stale state annotation")
        if not scenario["prompt"] or not scenario["reference"]:
            raise ValueError("Empty text")
    for pair in bundle["pairs"]:
        a, b = [bundle["scenarios"][r] for r in pair["roles"]]
        actual = [k for k in a["facts"] if a["facts"][k] != b["facts"][k]]
        if pair["changed"] != actual:
            raise ValueError("Wrong changed-fact annotation")
        if pair["kind"] == "effective" and a["facts"]["action"] == b["facts"]["action"]:
            raise ValueError("Ineffective intervention")
        if pair["kind"] == "noop" and actual:
            raise ValueError("No-op changed scored facts")
        edits = [k for k in a["world"] if a["world"][k] != b["world"][k]]
        if edits != [pair["intervention_field"]]:
            raise ValueError("Pair must change exactly one premise")
    base, noop, control = [bundle["scenarios"][r] for r in ("base", "noop", "surface")]
    if control["facts"] != base["facts"] or control["reference"] != base["reference"]:
        raise ValueError("Nuisance control changed the decision target")
    fields = [k for k in base["world"] if base["world"][k] != control["world"][k]]
    if fields != ["background_clock"]:
        raise ValueError("Nuisance control must change only the unrelated clock")
    if (
        not len(base["prompt"].encode())
        == len(noop["prompt"].encode())
        == len(control["prompt"].encode())
    ):
        raise ValueError("Unmatched byte lengths")
    if sum(a != b for a, b in zip(base["prompt"], noop["prompt"])) != sum(
        a != b for a, b in zip(base["prompt"], control["prompt"])
    ):
        raise ValueError("Unmatched numeric edit counts")


def prepare(
    output, *, train_sources=6000, validation_sources=400, test_sources=400, seed=2026
):
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    if min(train_sources, validation_sources, test_sources) < 1:
        raise ValueError("Nonempty splits required")
    output.mkdir(parents=True)
    counts = {
        "train": train_sources,
        "validation": validation_sources,
        "test": test_sources,
    }
    hashes = {}
    all_ids = set()
    seen_prompts = set()
    duplicate_draws = 0
    for split, count in counts.items():
        rows = []
        for i in range(count):
            attempt = 0
            while True:
                row = make_bundle(f"q3a-{split}-{i:06d}", split, f"{seed}/{attempt}", i)
                key = signature(row["scenarios"]["base"]["prompt"])
                if key not in seen_prompts:
                    break
                attempt += 1
                duplicate_draws += 1
                if attempt > 1000:
                    raise ValueError("Unique source space exhausted")
            seen_prompts.add(key)
            rows.append(row)
        ids = {r["source_id"] for r in rows}
        if ids & all_ids:
            raise ValueError("Source leakage")
        all_ids.update(ids)
        file = output / f"{split}.jsonl"
        write_rows(file, rows)
        hashes[file.name] = sha256(file)
    manifest = {
        "schema_version": 1,
        "seed": seed,
        "counts": counts,
        "sha256": hashes,
        "origin": "controlled synthetic, not human-authored",
        "surface_family_disjoint": True,
        "template_revision": "selective-v4-numeric-nuisance-control",
        "duplicate_source_draws_rejected": duplicate_draws,
        "generator_code_sha256": source_sha256(__file__),
        "naturalistic_transfer": "requires separately registered licensed sources and real labels",
        "human_labels_collected": False,
    }
    manifest["dataset_id"] = signature(manifest)
    write_json(output / "manifest.json", manifest)
    write_json(
        output / "test.lock.json",
        {
            "dataset_id": manifest["dataset_id"],
            "sha256": hashes["test.jsonl"],
            "selection_frozen": False,
            "purpose": "integrity only; not preregistration",
        },
    )
    return manifest


def verify_dataset(directory):
    directory = Path(directory)
    manifest = read_json(directory / "manifest.json")
    check = dict(manifest)
    expected = check.pop("dataset_id")
    if signature(check) != expected:
        raise ValueError("Manifest checksum mismatch")
    lock = read_json(directory / "test.lock.json")
    if (
        lock["dataset_id"] != expected
        or lock["sha256"] != manifest["sha256"]["test.jsonl"]
    ):
        raise ValueError("Test integrity lock mismatch")
    ids = set()
    families = {}
    texts = set()
    for split, count in manifest["counts"].items():
        file = directory / f"{split}.jsonl"
        if sha256(file) != manifest["sha256"][file.name]:
            raise ValueError(f"Changed split: {split}")
        rows = read_rows(file)
        if len(rows) != count:
            raise ValueError("Count mismatch")
        families[split] = set()
        for r in rows:
            validate_bundle(r)
            if r["split"] != split or r["source_id"] in ids:
                raise ValueError("Source/split leakage")
            ids.add(r["source_id"])
            families[split].add(r["surface_family"])
            # Duplicate base prompts across splits indicate more than shared names.
            key = signature(r["scenarios"]["base"]["prompt"])
            if key in texts:
                raise ValueError("Duplicate base prompt")
            texts.add(key)
    if any(
        families[a] & families[b]
        for a, b in [("train", "validation"), ("train", "test"), ("validation", "test")]
    ):
        raise ValueError("Surface families overlap")
    return manifest


def arm_examples(bundles, arm):
    if arm not in ARM_ROLES:
        raise ValueError("Unknown arm")
    return [
        {"source_id": b["source_id"], "role": role, **b["scenarios"][role]}
        for b in bundles
        for role in ARM_ROLES[arm]
    ]
