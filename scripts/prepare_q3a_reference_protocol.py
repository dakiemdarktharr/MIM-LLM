"""Reconstruct private reference prompts from pinned validation source IDs.

The public recipe contains hashes/IDs rather than copied corpus text. This
must recreate the exact pre-generation manifest, not choose new prompts.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipe", required=True)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(output)
    recipe = json.loads(Path(args.recipe).read_text(encoding="utf-8"))
    corpus = Path(args.corpus)
    with corpus.open("rb") as stream:
        if (
            hashlib.file_digest(stream, "sha256").hexdigest()
            != recipe["source_corpus_sha256"]
        ):
            raise ValueError("Original corpus bytes changed")
    originals = {
        row["source_id"]: row
        for row in (
            json.loads(line) for line in corpus.read_text(encoding="utf-8").splitlines()
        )
        if row["split"] == "validation"
    }
    prompts = {}
    suffix = "\nContinue this story in three to five sentences.\nContinuation:\n"
    for item in recipe["sources"]:
        source = item["source_id"]
        parts = re.findall(r"[^.!?]+[.!?]", originals[source]["text"])
        prompt = " ".join(p.strip() for p in parts[:2]) + suffix
        if hashlib.sha256(prompt.encode("utf-8")).hexdigest() != item["prompt_sha256"]:
            raise ValueError("Declared prompt changed")
        prompts[source] = prompt
    if len(prompts) != 16:
        raise ValueError("Require all sixteen declared sources")
    private = {
        k: v
        for k, v in recipe.items()
        if k
        not in {
            "source_corpus_sha256",
            "private_manifest_sha256",
            "private_manifest_newline",
        }
    }
    private["sources"] = prompts
    serialized = json.dumps(private, indent=2, ensure_ascii=False) + "\n"
    if recipe["private_manifest_newline"] == "CRLF":
        serialized = serialized.replace("\n", "\r\n")
    elif recipe["private_manifest_newline"] != "LF":
        raise ValueError("Unknown pre-generation manifest newline convention")
    payload = serialized.encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    if digest != recipe["private_manifest_sha256"]:
        raise ValueError(
            "Private manifest differs from original pre-generation declaration"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(payload)
    print(
        json.dumps(
            {
                "sources": len(prompts),
                "private_manifest_sha256": digest,
                "optimizer_updates": 0,
                "generated_samples": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
