# Windows runbook (verified 2026-11-25)

Use PowerShell in the repository root. The commands below create artifacts under `artifacts/`, which Git ignores. No paid API or cloud GPU is required. The observed GPU is **RTX 5050 Laptop 8 GB**, with PyTorch 2.10.0+cu128 working locally. [PyTorch's official installer](https://pytorch.org/get-started/locally/) is the source for future CUDA package updates.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install torch==2.10.0 --index-url https://download.pytorch.org/whl/cu128
.\.venv\Scripts\python.exe -m pip install -e ".[data,test]"
.\.venv\Scripts\python.exe -m pytest -q
nvidia-smi
```

The first commands below are bounded smoke/data-preparation operations, not a long study. TinyStories is a public dataset of generated short stories, licensed CDLA-Sharing-1.0 according to its [dataset card](https://huggingface.co/datasets/roneneldan/TinyStories). The importer pins its revision and records a manifest. It uses official train and validation splits, then reserves distinct validation rows for the project's test split.

```powershell
.\.venv\Scripts\mimlm.exe fetch-tinystories artifacts\pilot\tinystories.jsonl --train-stories 3000 --validation-stories 300 --test-stories 300
.\.venv\Scripts\mimlm.exe train-tokenizer --corpus artifacts\pilot\tinystories.jsonl --output artifacts\pilot\bpe.model --vocab-size 2048
.\.venv\Scripts\mimlm.exe matrix --corpus artifacts\pilot\tinystories.jsonl --tokenizer-model artifacts\pilot\bpe.model --output artifacts\pilot\first-pair --reference-width 192 --context 256 --kinds mim,mim_pair --seeds 0,1,2 --max-train-tokens 100000
```

`matrix` above writes a **dry-run plan**. Inspect the actual parameter counts and gaps first. Add `--run` only when the local throughput test supports the proposed budget; the plan records each completed run. `mimlm train --resume` restores a partially completed run from `latest.pt` if all settings and input hashes match. By default a checkpoint is saved every 100 optimizer updates and after validation. Use a new output directory for a fresh run. No model weights or raw corpus are committed.

The `--context 256` setting above is a cheap pilot setting. For the full 3–5 sentence and self-event comparison, measure the tokenized prompt and reserve room for both continuations and the follow-up instruction before fixing a common context for every system. The Transformer evaluator checks this worst-case length before generation; a larger context must be measured for memory and throughput on this laptop. Completed checkpoints require their exact tokenizer sidecar and checksum for generation or scoring.

Create and lock the paired synthetic pilot. Its first 100 pairs contain 2–5 key-holder changes; each pair changes only one premise. This is an executable pilot and cannot, by itself, support the Q3 benchmark claim.

```powershell
.\.venv\Scripts\mimlm.exe make-benchmark artifacts\pilot\pairs.jsonl --pairs 100
.\.venv\Scripts\mimlm.exe lock-benchmark --benchmark artifacts\pilot\pairs.jsonl --output artifacts\pilot\pairs.lock.json
.\.venv\Scripts\mimlm.exe evaluate --checkpoint artifacts\pilot\first-pair\mim-seed0\best.pt --benchmark artifacts\pilot\pairs.jsonl --lock-file artifacts\pilot\pairs.lock.json --output artifacts\pilot\mim-eval.jsonl --split validation --self-events
.\.venv\Scripts\mimlm.exe evaluate --checkpoint artifacts\pilot\first-pair\mim_pair-seed0\best.pt --benchmark artifacts\pilot\pairs.jsonl --lock-file artifacts\pilot\pairs.lock.json --output artifacts\pilot\pair-eval.jsonl --split validation --self-events
.\.venv\Scripts\mimlm.exe blind-packet --generations artifacts\pilot\mim-eval.jsonl artifacts\pilot\pair-eval.jsonl --output artifacts\pilot\packet.jsonl --key-output artifacts\pilot\private-key.jsonl
```

Two readers independently fill copies of `packet.jsonl`. `private-key.jsonl` must stay concealed from them. Each reader checks all mandatory propositions, contradictions, 3–5 sentence form, counterfactuals, retained facts, concrete new events and fluency. If a second continuation exists, the reader first records a **state table after the model's first generated text** in `self_event_state_after_first`, then judges the second text against it. A generic first text with no concrete event should not receive self-event credit. No script invents these judgments.

```powershell
.\.venv\Scripts\mimlm.exe agreement --rater-a artifacts\pilot\reader-a.jsonl --rater-b artifacts\pilot\reader-b.jsonl
.\.venv\Scripts\mimlm.exe adjudication-packet --rater-a artifacts\pilot\reader-a.jsonl --rater-b artifacts\pilot\reader-b.jsonl --output artifacts\pilot\adjudication.jsonl
# A human resolves every null field in adjudication.jsonl.
.\.venv\Scripts\mimlm.exe finalize-adjudication --packet artifacts\pilot\adjudication.jsonl --output artifacts\pilot\final-labels.jsonl
.\.venv\Scripts\mimlm.exe aggregate-labels --labels artifacts\pilot\final-labels.jsonl --key artifacts\pilot\private-key.jsonl
.\.venv\Scripts\mimlm.exe perplexity --checkpoint artifacts\pilot\first-pair\mim-seed0\best.pt --corpus artifacts\pilot\tinystories.jsonl --split test
```

The final locked test split is evaluated **once after model and decoding selection**. Before that, use validation. A complete paper run also needs a separately licensed human-written story sample, adjudicated annotations, multiple seeds, fluent 3–5 sentence outputs and cost-matched analyses. Keep all generated text, decoding settings, corpus/tokenizer hashes, run manifests and annotation decisions with the experiment record.

For a new resource budget, measure on this machine. Approximate GPU-hours as
\(\sum_{model,seed} N_{train}/r_{train} / 3600\), then add measured validation and generation time; \(r_{train}\) is the **sustained** token throughput from that architecture on this GPU. The present 339-token and 1,024-token runs are only smoke tests, so the full-study GPU-hour budget is **not measured yet**. `peak_vram_bytes` and `peak_vram_reserved_bytes` are PyTorch allocator figures, not total device consumption reported by `nvidia-smi`.
