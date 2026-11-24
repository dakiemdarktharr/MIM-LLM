# MIM-LLM

**Status: research planning.** This repository is the starting point for a software-only research program on autoregressive story continuation. It contains no trained model, benchmark result, submitted manuscript, or publication yet.

## Research question

MIM-LLM investigates whether the **Memory In Memory (MIM)** mechanism introduced by Yunbo Wang and colleagues for video prediction at CVPR 2019 can improve the logical consistency of a small next-token language model. The original [paper](https://arxiv.org/abs/1811.07490) and [author code](https://github.com/Yunbo426/MIM) are the methodological starting points, not contributions of this project.

The proposed prototype is called **MIM-LM**. Its exact trainable parameter count will be reported from the implemented model, alongside its tokenizer, training tokens, estimated FLOPs, VRAM use, throughput, and GPU-hours. The initial planning range is approximately 1–5 million parameters; it is not a measured model size.

**Hypothesis.** Under matched input information and training resources, explicitly differencing consecutive lower-layer hidden states and passing that signal through MIM-N and MIM-S will reduce contradictions in generated continuations, particularly after repeated state changes and when actual and counterfactual situations must remain separate. A strong alternative is that a learned projection of the *pair* of consecutive hidden states, or a simpler recurrent model, will do as well or better. The experiments will test both possibilities and report negative results.

## Task and illustrative example

The input is a story prefix plus an instruction to continue it. The target output is **three to five natural sentences** that may express temporal, causal, conditional, or counterfactual relations. Single-name answers are useful component probes, but they are not the target task.

> **Illustrative input, not a model result.** A cabinet is locked. Lan gives the key to Huy, and Huy passes it to Mai. At exactly 9:00, whoever holds the key must open the cabinet if electricity has returned; otherwise they must wait. Electricity returns at 8:55. Continue the scene and explain what would differ if it returned ten minutes later.
>
> **One valid illustrative continuation, not a model result.** At 9:00, Mai opens the cabinet because she holds the key and power has returned. She puts the key in a drawer. When Lan asks for it, Mai points her to that drawer. If power had returned at 9:05, the cabinet would still have been locked at 9:00; Mai would have had to wait.

The model may choose another coherent place for the key. Evaluation must respect facts the model itself adds. A paired test changes only `8:55` to `9:05`: the cabinet-opening event at 9:00 must change, while the key transfers and Mai's ownership at 9:00 remain true.

## Planned model

```text
tokens → embedding → base recurrent layer → MIM-N(Δ hidden state)
       → MIM-S(temporal memory) → recurrent output → LM head → next-token logits
```

The original MIM uses convolutional ST-LSTM cells and an additional zigzag spatiotemporal memory for image sequences. Replacing image convolutions with vector projections and deciding whether to retain an analogue of that extra memory are **our proposed language-model variants**. No claim of faithful equivalence or improved performance is made before implementation and ablation.

## Evaluation plan

- Compare LSTM, Nested LSTM, a small Transformer, a suitable modern recurrent baseline, full MIM-LM, MIM-N/MIM-S ablations, and a key control that receives both consecutive hidden states and learns a mixing or projection function. A token-shift-only control will be named as such, rather than called a full RWKV model.
- Match tokenizer, corpus, train/validation split, training-token budget, and decoding policy. Report both near-parameter-matched and near-compute-matched comparisons where they differ.
- Pre-register the primary measure: the fraction of continuations satisfying all required propositions without contradicting their actual generated history. Also report coverage, contradiction type, fluency, held-out perplexity, per-seed results, and uncertainty grouped by source story or paired story.
- Evaluate self-generated events by fixing the model's first continuation verbatim, then asking it to continue again. Record whether it avoids concrete events or writes only generic text. Use blinded human review on a representative sample; human labels will never be fabricated.
- Keep gold state tables for scoring intrinsic-memory experiments at inference. State supervision during training will be a separately labeled ablation.

## Conditional publication roadmap

These are **working manuscript directions**, not publication claims. Each requires an independent question and sufficient evidence; directions may be revised, merged, or stopped.

1. **Q3-A — State-change and counterfactual continuation benchmark:** construct and validate a benchmark that accepts multiple coherent continuations and distinguishes required changes from preserved facts.
2. **Q3-B — State supervision versus intrinsic memory:** test whether explicit state supervision at training changes consistency and generalization compared with unassisted recurrent memory.
3. **Q3-C — Recurrent memory mechanisms under local compute limits:** analyze MIM-N/MIM-S ablations, learned-pair controls, efficiency, and failure modes.
4. **Q1 — MIM-LM architecture study:** submit only if rigorous, resource-matched evidence demonstrates a broadly relevant contribution beyond the component studies. It need not wait for the other manuscripts.

For every manuscript, track **drafted**, **submitted**, **accepted**, and **published** as separate, evidence-backed milestones. Journal fit, fees, indexing, and subject-specific quartiles must be checked again at submission. The publication budget is 0 VND; no paid API or cloud GPU is assumed.

## Next steps

1. Record a dated literature and novelty search, including close prior work and the limits of the search.
2. Specify the model equations, state reset and masking rules, dataset provenance, and paired benchmark scoring protocol.
3. Implement the PyTorch prototype on Windows, then verify small-batch overfitting, causal masking, and agreement between full-sequence and stepwise evaluation.
4. Measure actual RTX 3060 12 GB throughput and memory before scheduling larger runs. Prioritize a strong learned-pair control against full MIM-LM.

## Achievements

- Repository initialized with this research plan. No scientific or editorial outcome has yet been established.
