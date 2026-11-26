"""Private, offline inference diagnostic for a pinned published TinyStories LM.

Not a matched-data/compute comparison, an unseen test, or a training parent.
Install Transformers into a separate target directory; never import custom
model code. All prompts and decoding are declared before reference generation.
"""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-dir", required=True)
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--tokenizer-dir", required=True)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    setup = output.with_suffix(".setup.json")
    summary_path = output.with_suffix(".summary.json")
    if any(p.exists() for p in (output, setup, summary_path)):
        raise FileExistsError("Use a new diagnostic output path")
    protocol = json.loads(Path(args.protocol).read_text(encoding="utf-8"))
    if (
        len(protocol["sources"]) != 16
        or protocol["optimizer_updates"] != 0
        or protocol["primary_evaluation"]
        or not protocol["declared_before_generation"]
    ):
        raise ValueError("Require the declared sixteen-source inference protocol")
    model_dir = Path(args.model_dir).resolve()
    if digest(model_dir / "pytorch_model.bin") != protocol["weights_sha256"]:
        raise ValueError("External checkpoint bytes changed")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    sys.path.insert(0, str(Path(args.runtime_dir).resolve()))
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if transformers.__version__ != protocol["transformers"]:
        raise ValueError("Require the declared Transformers version")
    torch.set_num_threads(protocol["cpu_threads"])
    tokenizer = AutoTokenizer.from_pretrained(
        Path(args.tokenizer_dir).resolve(),
        local_files_only=True,
        trust_remote_code=False,
    )
    model, loading = AutoModelForCausalLM.from_pretrained(
        model_dir,
        local_files_only=True,
        trust_remote_code=False,
        weights_only=True,
        attn_implementation="eager",
        output_loading_info=True,
    )
    loading = {
        key: sorted(value) if isinstance(value, set) else value
        for key, value in loading.items()
    }
    # Old Transformers persisted attention masks as state_dict buffers.
    import re

    unexpected = loading.get("unexpected_keys", [])
    missing = loading.get("missing_keys", [])
    if (
        missing
        or loading.get("mismatched_keys")
        or any(
            not re.fullmatch(
                r"transformer\.h\.\d+\.attn\.attention\.(bias|masked_bias)", key
            )
            for key in unexpected
        )
    ):
        raise ValueError(f"Checkpoint load mismatch: {loading}")
    model.eval()
    parameters = sum(p.numel() for p in model.parameters())
    token_embedding_parameters = model.get_input_embeddings().weight.numel()
    declaration = {
        "protocol_sha256": digest(args.protocol),
        "script_sha256": digest(__file__),
        "model_id": protocol["model_id"],
        "revision": protocol["model_revision"],
        "weights_sha256": protocol["weights_sha256"],
        "actual_parameters": parameters,
        "token_embedding_parameters": token_embedding_parameters,
        "vocab_size": len(tokenizer),
        "configured_position_limit": model.config.max_position_embeddings,
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "device": "cpu",
        "load_report": loading,
        "optimizer_updates": 0,
        "tokenizer_fitted": False,
        "training_overlap_unverified": True,
        "model_weight_license_unresolved": True,
        "primary_evaluation": False,
        "human_labels": False,
        "scope": "External reference inference only; not a matched or unseen scientific comparison",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with setup.open("x", encoding="utf-8") as stream:
        json.dump(declaration, stream, indent=2)
    print(json.dumps(declaration), flush=True)
    decoding = protocol["decoding"].copy()
    seed = decoding.pop("seed")
    suffix = "\nContinue this story in three to five sentences.\nContinuation:\n"
    started = time.perf_counter()
    with torch.inference_mode(), output.open("x", encoding="utf-8") as stream:
        for source, original in sorted(protocol["sources"].items()):
            if not original.endswith(suffix):
                raise ValueError("Original prefix format changed")
            for condition in protocol["conditions"]:
                prompt = (
                    original
                    if condition == "prefix_and_instruction"
                    else original[: -len(suffix)] + " "
                )
                ids = tokenizer(prompt, return_tensors="pt").input_ids
                if (
                    ids.shape[1] + decoding["max_new_tokens"]
                    > model.config.max_position_embeddings
                ):
                    raise ValueError("No prompt truncation allowed")
                torch.manual_seed(seed)
                generated = model.generate(
                    ids,
                    **decoding,
                    use_cache=True,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                )
                emitted = generated[0, ids.shape[1] :].tolist()
                text = tokenizer.decode(emitted, skip_special_tokens=True)
                row = {
                    "source_id": source,
                    "condition": condition,
                    "prompt": prompt,
                    "continuation": text,
                    "token_ids": emitted,
                    "seed": seed,
                    "generated_token_count_including_eos": len(emitted),
                    "primary_evaluation": False,
                    "human_label": None,
                }
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                stream.flush()
                print(
                    json.dumps(
                        {
                            "source_id": source,
                            "condition": condition,
                            "generated_tokens": len(emitted),
                        }
                    ),
                    flush=True,
                )
    if digest(model_dir / "pytorch_model.bin") != protocol["weights_sha256"]:
        raise ValueError("Weights changed during read-only diagnostic")
    with summary_path.open("x", encoding="utf-8") as stream:
        json.dump(
            {
                **declaration,
                "samples": 32,
                "elapsed_seconds": time.perf_counter() - started,
                "output_sha256": digest(output),
                "complete": True,
            },
            stream,
            indent=2,
        )


if __name__ == "__main__":
    main()
