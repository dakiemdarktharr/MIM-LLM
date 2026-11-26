"""Blank author-reader packet for the fixed foundation feasibility review.

This hides run identifiers, not the author's prior knowledge. It neither
collects real labels nor establishes independent/inter-rater validation.
"""

import csv
import random
import re
from pathlib import Path

from ..q3a.io import (
    read_json,
    read_rows,
    sha256,
    signature,
    source_sha256,
    write_json,
    write_rows,
)
from . import inference

FIELDS = (
    "item_id",
    "rater_id",
    "format_3_to_5",
    "fluency_1_to_5",
    "follows_prefix",
    "new_event",
    "self_consistent",
    "unclear",
    "evidence",
    "elapsed_seconds",
)


def reader_markdown(rows):
    """Show exact blinded text without treating generated Markdown as markup."""
    parts = [
        "# Foundation writing: blinded author-reader packet\n\n",
        (
            "Read each prompt and continuation, then fill reader-author.csv. "
            "Empty outputs remain empty. Keep PRIVATE-key.jsonl closed until "
            "ratings are saved. No human ratings are prefilled.\n\n"
        ),
    ]
    for row in rows:
        if not re.fullmatch(r"item-\d{4}", row["item_id"]):
            raise ValueError("Unexpected blinded item identifier")
        parts.append(f"## {row['item_id']}\n\n")
        for field, title in (("prompt", "Prompt"), ("continuation", "Continuation")):
            text = row[field]
            fence = "`" * max(
                3, 1 + max((len(s) for s in re.findall(r"`+", text)), default=0)
            )
            parts.append(f"**{title}**\n\n{fence}text\n{text}\n{fence}\n\n")
    return "".join(parts)


def checked_samples(directory, manifest):
    directory = Path(directory)
    review = read_json(manifest)
    if signature({k: v for k, v in review.items() if k != "review_id"}) != review.get(
        "review_id"
    ):
        raise ValueError("Changed review manifest")
    started = read_json(directory / "started.json")
    completed = read_json(directory / "completed.json")
    rows = read_rows(directory / "samples.jsonl")
    if (
        completed.get("complete") is not True
        or completed.get("samples") != 34
        or len(rows) != 34
        or review.get("expected_samples") != 34
        or len(review.get("prompts", [])) != 17
        or started.get("manifest_sha256") != sha256(manifest)
        or completed.get("samples_sha256") != sha256(directory / "samples.jsonl")
        or started.get("review_id") != review["review_id"]
        or completed.get("review_id") != review["review_id"]
        or started.get("plan_id") != review["plan_id"]
        or review.get("inference_backend") != inference.BACKEND
        or review.get("inference_source_sha256") != source_sha256(inference.__file__)
        or started.get("inference_backend") != inference.BACKEND
        or started.get("inference_source_sha256") != source_sha256(inference.__file__)
    ):
        raise ValueError("Only a complete, unchanged real review may be packaged")
    parents = started["checkpoint_sha256"]
    if set(parents) != {"foundation-mingru-s0", "foundation-transformer-s0"}:
        raise ValueError("Require both declared parents")
    prompts = {(p["condition"], p["source_id"]): p["prompt"] for p in review["prompts"]}
    if (
        len(prompts) != 17
        or sum(k[0] == "conditional" and k[1] is not None for k in prompts) != 16
        or ("unconditional", None) not in prompts
    ):
        raise ValueError("Require sixteen validation prefixes and one unconditional")
    observed = set()
    for row in rows:
        key = (row["run_id"], row["condition"], row["source_id"])
        if key in observed:
            raise ValueError("Duplicate review item")
        observed.add(key)
        if (
            row["run_id"] not in parents
            or row["checkpoint_sha256"] != parents[row["run_id"]]
            or row.get("review_id") != review["review_id"]
            or row.get("plan_id") != review["plan_id"]
            or row["prompt"] != prompts.get((row["condition"], row["source_id"]))
            or row.get("human_label") is not None
            or row.get("primary_evaluation") is not False
            or not isinstance(row.get("continuation"), str)
            or row.get("inference_backend") != inference.BACKEND
        ):
            raise ValueError("Review row differs from its declared provenance")
    if observed != {
        (run, condition, source) for run in parents for condition, source in prompts
    }:
        raise ValueError("Incomplete fixed review panel")
    return rows, review


def make_packet(directory, manifest, output, *, seed=2026):
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    rows, review = checked_samples(directory, manifest)
    random.Random(seed).shuffle(rows)
    public, key = [], []
    for i, row in enumerate(rows):
        item_id = f"item-{i:04d}"
        public.append(
            {
                "item_id": item_id,
                "prompt": row["prompt"],
                "continuation": row["continuation"],
            }
        )
        key.append(
            {
                "item_id": item_id,
                **{
                    k: row[k]
                    for k in (
                        "run_id",
                        "condition",
                        "source_id",
                        "checkpoint_sha256",
                        "review_id",
                        "plan_id",
                    )
                },
            }
        )
    output.mkdir(parents=True)
    write_rows(output / "packet.jsonl", public)
    write_rows(output / "PRIVATE-key.jsonl", key)
    (output / "reader-packet.md").write_text(
        reader_markdown(public), encoding="utf-8", newline="\n"
    )
    with (output / "reader-author.csv").open(
        "x", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in public:
            writer.writerow({"item_id": row["item_id"]})
    (output / "GUIDE.md").write_text(
        "# Foundation writing feasibility: author-reader packet\n\n"
        "No ratings have been collected or prefilled. Keep PRIVATE-key.jsonl "
        "closed until ratings are saved. Model IDs are hidden, but this remains "
        "author evaluation, not independent validation. Do not calculate "
        "inter-rater agreement from one reader.\n\n"
        "Read each full prompt and continuation, including empty, repetitive "
        "or truncated samples. Rate format_3_to_5, follows_prefix, new_event, "
        "self_consistent and unclear as 0/1; fluency_1_to_5 as 1..5. For the "
        "unconditional prompt, follows_prefix means obeying the supplied request. "
        "An intelligible new action counts as an event; generic scene wording "
        "alone does not. Check later assertions against the prompt and earlier "
        "generated assertions. A fluent but contradictory story is not logically "
        "consistent. Explain judgments/ambiguity with an evidence span or an "
        "omission note, give your real rater ID and record actual elapsed_seconds. "
        "Do not infer correctness from the model identity or invented references.\n\n"
        "This small validation panel informs writing feasibility. It is not the "
        "locked primary logic test, a calibrated population estimate, or a passed "
        "writing gate by itself. Declare any decision rule before inspecting "
        "the generated panel; preserve failures and original ratings.\n",
        encoding="utf-8",
        newline="\n",
    )
    result = {
        "items": len(public),
        "shuffle_seed": seed,
        "review_id": review["review_id"],
        "source_samples_sha256": sha256(Path(directory) / "samples.jsonl"),
        "packet_sha256": sha256(output / "packet.jsonl"),
        "presentation_version": 2,
        "reader_markdown_sha256": sha256(output / "reader-packet.md"),
        "real_labels_collected": 0,
        "reader_count_available": 1,
        "independent_reader_validation": False,
        "writing_gate_passed": None,
    }
    write_json(output / "receipt.json", result)
    return result
