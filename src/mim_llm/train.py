"""Reproducible local training with explicit token and compute accounting."""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import shutil
import time
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.utils.data import DataLoader

from .data import StoryDataset, collate, load_jsonl
from .models import ModelConfig, build_model, cross_entropy, parameter_count
from .tokenizer import load_tokenizer


def seed_everything(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def device_name(requested: str) -> str:
    if requested == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    return requested


@torch.inference_mode()
def evaluate_loss(
    model: nn.Module, loader: DataLoader, device: torch.device
) -> dict[str, float]:
    model.eval()
    weighted_loss = 0.0
    tokens = 0
    for batch in loader:
        inputs = batch["input_ids"].to(device)
        targets = batch["targets"].to(device)
        mask = batch["attention_mask"].to(device)
        logits, _ = model(inputs, mask)
        count = int((targets != -100).sum().item())
        weighted_loss += float(cross_entropy(logits, targets).item()) * count
        tokens += count
    if tokens == 0:
        raise ValueError("Validation split has no tokens")
    loss = weighted_loss / tokens
    return {
        "loss": loss,
        "perplexity": math.exp(loss) if loss < 80 else float("inf"),
        "tokens": tokens,
    }


def train(
    corpus: str | Path,
    output_dir: str | Path,
    config: ModelConfig,
    *,
    seed: int = 0,
    batch_size: int = 8,
    learning_rate: float = 3e-4,
    max_train_tokens: int = 100_000,
    grad_clip: float = 1.0,
    state_loss_weight: float = 0.0,
    device: str = "auto",
    tokenizer_model: str | None = None,
    resume: bool = False,
    checkpoint_every_updates: int = 100,
) -> dict[str, Any]:
    if (
        batch_size < 1
        or max_train_tokens < 1
        or learning_rate <= 0
        or checkpoint_every_updates < 1
    ):
        raise ValueError("Invalid training settings")
    if state_loss_weight and config.state_classes < 2:
        raise ValueError("State supervision requires state_classes >= 2")
    seed_everything(seed)
    device = torch.device(device_name(device))
    rows = load_jsonl(corpus)
    tokenizer = load_tokenizer(tokenizer_model)
    if tokenizer_model is not None:
        config = replace(config, vocab_size=tokenizer.vocab_size)
    elif config.vocab_size != tokenizer.vocab_size:
        raise ValueError("Byte tokenizer requires vocab_size=259")
    train_set = StoryDataset(rows, tokenizer, "train", config.context)
    valid_set = StoryDataset(rows, tokenizer, "validation", config.context)
    if not train_set or not valid_set:
        raise ValueError("Corpus needs nonempty train and validation splits")
    valid_loader = DataLoader(
        valid_set, batch_size=batch_size, collate_fn=collate, num_workers=0
    )
    model = build_model(config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    count = parameter_count(model)
    output = Path(output_dir)
    if not resume and output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Output directory already contains files: {output}")
    output.mkdir(parents=True, exist_ok=True)
    if tokenizer_model is not None and not resume:
        shutil.copyfile(tokenizer_model, output / "tokenizer.model")
    started = time.perf_counter()
    train_seconds = 0.0
    validation_seconds = 0.0
    trained_tokens = 0
    updates = 0
    best = float("inf")
    epoch = 0
    cursor = 0
    elapsed_previous = 0.0
    peak_previous = 0
    peak_reserved_previous = 0
    corpus_sha = file_sha256(corpus)
    tokenizer_sha = file_sha256(tokenizer_model) if tokenizer_model else None
    if resume:
        copied_tokenizer = output / "tokenizer.model"
        if tokenizer_sha is not None and (
            not copied_tokenizer.exists()
            or file_sha256(copied_tokenizer) != tokenizer_sha
        ):
            raise ValueError("Resumable run has a missing or changed tokenizer copy")
        latest_file = output / "latest.pt"
        if not latest_file.exists():
            raise FileNotFoundError(f"No resumable checkpoint: {latest_file}")
        latest = torch.load(latest_file, map_location=device, weights_only=True)
        expected = {
            "config": asdict(config),
            "seed": seed,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "max_train_tokens": max_train_tokens,
            "state_loss_weight": state_loss_weight,
            "grad_clip": grad_clip,
            "corpus_sha256": corpus_sha,
            "tokenizer_sha256": tokenizer_sha,
            "device": str(device),
        }
        if any(latest.get(key) != value for key, value in expected.items()):
            raise ValueError("Resume settings or input hashes differ from checkpoint")
        model.load_state_dict(latest["model"])
        optimizer.load_state_dict(latest["optimizer"])
        trained_tokens, updates = latest["trained_tokens"], latest["updates"]
        epoch, cursor, best = latest["epoch"], latest["cursor"], latest["best"]
        train_seconds, validation_seconds = (
            latest["train_seconds"],
            latest["validation_seconds"],
        )
        elapsed_previous = latest["elapsed_seconds"]
        peak_previous = latest.get("peak_vram_bytes", 0)
        peak_reserved_previous = latest.get("peak_vram_reserved_bytes", 0)
        torch.set_rng_state(latest["torch_rng"].cpu())
        if device.type == "cuda":
            torch.cuda.set_rng_state_all([state.cpu() for state in latest["cuda_rng"]])

    def save_latest(
        *, current_epoch: int, current_cursor: int, current_train_seconds: float
    ) -> None:
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        checkpoint = {
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "config": asdict(config),
            "seed": seed,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "max_train_tokens": max_train_tokens,
            "state_loss_weight": state_loss_weight,
            "grad_clip": grad_clip,
            "corpus_sha256": corpus_sha,
            "tokenizer_sha256": tokenizer_sha,
            "device": str(device),
            "trained_tokens": trained_tokens,
            "updates": updates,
            "epoch": current_epoch,
            "cursor": current_cursor,
            "best": best,
            "train_seconds": current_train_seconds,
            "validation_seconds": validation_seconds,
            "elapsed_seconds": elapsed_previous + time.perf_counter() - started,
            "peak_vram_bytes": max(
                peak_previous, torch.cuda.max_memory_allocated(device)
            )
            if device.type == "cuda"
            else 0,
            "peak_vram_reserved_bytes": max(
                peak_reserved_previous, torch.cuda.max_memory_reserved(device)
            )
            if device.type == "cuda"
            else 0,
            "torch_rng": torch.get_rng_state(),
            "cuda_rng": torch.cuda.get_rng_state_all() if device.type == "cuda" else [],
        }
        temp = output / "latest.tmp"
        torch.save(checkpoint, temp)
        os.replace(temp, output / "latest.pt")

    while trained_tokens < max_train_tokens:
        permutation = torch.randperm(
            len(train_set), generator=torch.Generator().manual_seed(seed + epoch)
        ).tolist()
        if cursor >= len(permutation):
            epoch, cursor = epoch + 1, 0
            continue
        model.train()
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        train_started = time.perf_counter()
        while cursor < len(permutation):
            selected = permutation[cursor : cursor + batch_size]
            batch = collate([train_set[index] for index in selected])
            cursor += len(selected)
            inputs = batch["input_ids"].to(device)
            targets = batch["targets"].to(device)
            mask = batch["attention_mask"].to(device)
            token_count = int(mask.sum().item())
            if token_count == 0:
                continue
            optimizer.zero_grad(set_to_none=True)
            logits, state_logits = model(inputs, mask)
            loss = cross_entropy(logits, targets)
            state_labels = batch["state_labels"].to(device)
            if state_loss_weight > 0:
                if int((state_labels != -100).sum()) == 0:
                    raise ValueError(
                        "State supervision requested but this batch has no state labels"
                    )
                if int(state_labels.max()) >= config.state_classes:
                    raise ValueError("State label exceeds state_classes")
                loss = loss + state_loss_weight * cross_entropy(
                    state_logits, state_labels
                )
            if not torch.isfinite(loss):
                raise FloatingPointError("Non-finite loss")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
            optimizer.step()
            trained_tokens += token_count
            updates += 1
            if updates % checkpoint_every_updates == 0:
                save_latest(
                    current_epoch=epoch,
                    current_cursor=cursor,
                    current_train_seconds=train_seconds
                    + time.perf_counter()
                    - train_started,
                )
            if trained_tokens >= max_train_tokens:
                break
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        train_seconds += time.perf_counter() - train_started
        validation_started = time.perf_counter()
        validation = evaluate_loss(model, valid_loader, device)
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        validation_seconds += time.perf_counter() - validation_started
        if validation["loss"] < best:
            best = validation["loss"]
            temp = output / "best.tmp"
            torch.save(
                {
                    "model": model.state_dict(),
                    "config": asdict(config),
                    "seed": seed,
                    "train_tokens": trained_tokens,
                    "validation": validation,
                    "tokenizer_sha256": tokenizer_sha,
                },
                temp,
            )
            os.replace(temp, output / "best.pt")
        epoch += 1
        cursor = 0
        save_latest(
            current_epoch=epoch,
            current_cursor=cursor,
            current_train_seconds=train_seconds,
        )
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    elapsed = elapsed_previous + time.perf_counter() - started
    manifest: dict[str, Any] = {
        "config": asdict(config),
        "seed": seed,
        "device": str(device),
        "gpu": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
        "torch": torch.__version__,
        "corpus": str(Path(corpus).resolve()),
        "corpus_sha256": corpus_sha,
        "parameters": count,
        "tokenizer": "sentencepiece_bpe" if tokenizer_model else "utf8_byte",
        "tokenizer_sha256": tokenizer_sha,
        "train_tokens_actual": trained_tokens,
        "train_tokens_requested": max_train_tokens,
        "updates": updates,
        "epochs": epoch,
        "seconds": elapsed,
        "tokens_per_train_second": trained_tokens / train_seconds,
        "tokens_per_wall_second": trained_tokens / elapsed,
        "train_seconds": train_seconds,
        "validation_seconds": validation_seconds,
        "gpu_hours": elapsed / 3600 if device.type == "cuda" else 0.0,
        "dense_train_flops_6p_rough_proxy": 6 * count * trained_tokens,
        "flops_note": "6*parameters*tokens is a rough dense-model proxy, not measured total FLOPs; embeddings, recurrent gating, and software overhead differ.",
        "peak_vram_bytes": max(peak_previous, torch.cuda.max_memory_allocated(device))
        if device.type == "cuda"
        else None,
        "peak_vram_reserved_bytes": max(
            peak_reserved_previous, torch.cuda.max_memory_reserved(device)
        )
        if device.type == "cuda"
        else None,
        "best_validation": best,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "state_loss_weight": state_loss_weight,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return manifest


def load_checkpoint(
    path: str | Path, *, device: str = "auto"
) -> tuple[nn.Module, dict[str, Any]]:
    device = device_name(device)
    checkpoint = torch.load(path, map_location=device, weights_only=True)
    config = ModelConfig(**checkpoint["config"])
    model = build_model(config).to(device)
    model.load_state_dict(checkpoint["model"])
    model.eval()
    return model, checkpoint


def load_checkpoint_tokenizer(checkpoint_path: str | Path, checkpoint: dict[str, Any]):
    """Load the exact tokenizer used for training or fail closed."""
    path = Path(checkpoint_path)
    manifest_path = path.parent / "manifest.json"
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.exists()
        else {}
    )
    expected_sha = checkpoint.get("tokenizer_sha256", manifest.get("tokenizer_sha256"))
    if (
        "tokenizer_sha256" in checkpoint
        and "tokenizer_sha256" in manifest
        and checkpoint["tokenizer_sha256"] != manifest["tokenizer_sha256"]
    ):
        raise ValueError("Checkpoint and manifest disagree on tokenizer checksum")
    tokenizer_path = path.parent / "tokenizer.model"
    if expected_sha is None:
        if tokenizer_path.exists():
            raise ValueError(
                "Unexpected tokenizer.model beside byte-tokenizer checkpoint"
            )
        tokenizer = load_tokenizer(None)
    else:
        if not tokenizer_path.exists() or file_sha256(tokenizer_path) != expected_sha:
            raise ValueError("Missing or changed tokenizer.model beside checkpoint")
        tokenizer = load_tokenizer(tokenizer_path)
    if tokenizer.vocab_size != checkpoint["config"]["vocab_size"]:
        raise ValueError("Tokenizer vocabulary size differs from checkpoint")
    return tokenizer
