> **Execution update, 26 November 2026:** The first two seed-0 baseline warm-ups completed on Colab T4, 5 million supervised byte targets each, but failed the qualitative writing check. One bounded language calibration is now running under plan `ef827ca21a627ce714caaea1d0ab52b293f858e526e654358bbb633c36328660`: Transformer completed 50M targets on L4; minGRU is resuming on T4 from its persisted checkpoint. Only these two seed-0 warm-ups are enabled. No A0–A3 post-training or final-test evaluation has run. See the [pilot report](docs/Q3_A_COLAB_PILOT_20261126.vi.md) and [calibration protocol](docs/Q3_A_CALIBRATION2_PROTOCOL.vi.md). B/C/Q1 and tokenizer fitting remain closed. Earlier zero-training receipts describe their original preparation sessions.

# MIM-LLM

**Status: research planning and language feasibility calibration.** This software-only
project studies autoregressive story continuation and recurrent language-model
memory. All three standalone Q3 studies now have preparation code, pinned data
plans, evaluation pipelines and non-optimizing checks. Q3-A training is limited
to its authorized calibration; further matrix expansion requires the writing
feasibility review. C's genuine model-history bank requires compatible shared
warm-up checkpoints; the branch-residual architecture remains a research design. No manuscript has been
submitted, accepted or published.

## Long-term objective

Build a MIM-based autoregressive language model capable of complete, natural
multi-turn conversation: following instructions, answering follow-up questions,
using earlier dialogue, respecting corrections and generating coherent responses
across topics. Early ChatGPT-style conversation is an aspirational reference,
not a measured capability or an equivalence claim.

The roadmap includes general language pretraining, supervised instruction/chat
fine-tuning, and separate evaluations of conversational usefulness, memory,
logic and factual reliability. Story continuation is an initial research task;
passing it or publishing papers does not establish a capable chat model. The
small prototypes are feasibility tools, with scaling dependent on measured
quality and resources. See the [capability objective and gates](docs/PROJECT_OBJECTIVE.vi.md).

## Methodological starting point

Memory In Memory (MIM), introduced by Yunbo Wang and colleagues at CVPR 2019,
uses consecutive lower-layer state differences and nested memories for video
prediction. The original [paper](https://arxiv.org/abs/1811.07490) and
[author code](https://github.com/Yunbo426/MIM) are prior work. A vector adaptation
alone does not establish a novel language architecture.

The implemented prototype is called **MIM-LM**. Its width-192, two-layer byte
configuration has **1,984,320** trainable parameters; the tested BPE-512 version
has **2,081,472**. These are actual counts for the legacy prototype. The proposed
branch-residual model is not implemented and has no measured parameter count.

## Task and illustrative example

The target is a **three-to-five-sentence natural continuation**, with writing
quality assessed separately from logical consistency. Single-name/state answers
are component probes only. Preserve multiple valid narrative choices and facts
the model itself introduces.

> **Illustration, not a model result.** A cabinet is locked. Lan gives its key to
> Huy, who passes it to Mai before 9:00. Everyone obeys the one-time rule: at
> exactly 9:00 the holder opens the cabinet if power has returned, otherwise waits.
> The cabinet stays locked until then. Power returns at 8:55.
>
> **One valid continuation, not a model result.** At 9:00 Mai opens the cabinet
> because power has returned. She puts the key in a drawer. When Lan asks for it,
> Mai points to that drawer. If power had returned at 9:05, Mai would have waited
> and the cabinet would still have been locked at 9:00.

Changing only 8:55 to 9:05 changes the required 9:00 action, while the earlier
transfers and possession immediately before the action remain true. Changing
8:50 to 8:55 is a no-op for that action, although the observed power-return time
does change. The one-time rule does not uniquely require opening at 9:05.

## Four standalone study designs

1. **Learning When a Premise Change Should Not Change a Story:** semantic no-op
   training versus byte/edit-matched irrelevant numeric-clock controls and an invariance adaptation.
2. **Tokens or State Changes?** token delay versus semantic-write interference
   under matched supervision and explicit processing-cost controls.
3. **Controlled Roll-In Distributions for State-Consistent Story Continuation:**
   frozen initialization-coupled versus peer histories in a controlled grammar
   bank, with unconstrained main evaluation and explicit overlap limits.
4. **Branch-Residual Nested Memory for Multi-World Language Modeling:** a candidate
   shared-fork state and compressed per-world residual architecture, tested against
   full copies, same-byte controls, learned-pair and modern recurrent alternatives.

These are conditional hypotheses, not established novelty or publication claims.
The three training studies each plan four arms, two backbones and three seeds,
with equal token/selection caps and equal GPU-hour caps chosen after profiling.
Earlier BPE-512/context-256 counting examples are historical. All three studies'
prepared fixed-byte/context-2048 minGRU has **2,099,864** parameters (width 662);
the Transformer has **2,119,408** (width 248). Initial warm-up throughput has been
measured; writing feasibility failed initially and is under bounded repair.
A pilot allocates 48M post-training targets per study,
with shared warm-up counted once and a separate 15% selection reserve.

See the [current design and budgets](docs/PORTFOLIO_V3.vi.md),
[adversarial novelty audit](docs/NOVELTY_AUDIT_V3.vi.md),
[planning manifest](papers/portfolio_v3.json),
[manuscript source guide](papers/README.md), and [status](docs/STATUS.md).
The planning notes are in Vietnamese; the four manuscript shells are in English.

## Existing code and verification

The earlier PyTorch prototype implements vector MIM, N/S/M ablations, a learned
projection of both consecutive states, LSTM, Nested LSTM, GRU, minGRU, Delta-RNN,
a small causal Transformer and a token-shift GRU. Token-shift GRU is **not** full
RWKV. Tokenization, training/resume and a synthetic smoke benchmark exist.
Q3-A's separate pipeline now implements paired response training, invariant-probe
JS, checkpointing, generation, blank blind annotation and source-paired analysis.
B/C add delayed QA branches, genuine frozen-history collection/matching,
unconstrained two-stage evaluation, blank blind annotation and clustered analysis.
Q3-A optimizer/overfit/resume checks and real language warm-ups have run.
B/C optimization remains unauthorized; no production C history bank is claimed. See the
[three-study handoff](docs/THREE_Q3_PRETRAIN_RUNBOOK.vi.md),
[preparation-only Colab notebook](notebooks/Three_Q3_Prepare_Colab.ipynb), [legacy runbook](docs/RUNBOOK.md) and
[original mechanism map](docs/RESEARCH.md) for their verified scope.

Keep tokenizers, source splits, input information, training exposure and decoding
controlled. Report actual parameters, state bytes, FLOP estimates, measured time,
VRAM and selection budget. Validate free-text scoring with real blinded labels;
score coverage/evasion as well as contradictions. Gold state tables are for
scoring at intrinsic-memory inference, not extra generator input. Freeze tests
before final configuration selection and report every seed and negative result.

## Next evidence gates

Audit novelty, data rights and semantics; establish writing and annotation
feasibility; profile the actual GPU and validate optimizer/overfit/resume behavior;
preregister contrasts and resource caps; then run the balanced pilots. Scale the
architecture only if strong controls and memory-quality trade-offs justify it.
Directions may be revised, merged or stopped. Reused artifacts and prior findings
must be disclosed and cited, without presenting an old result table as new.

The publication budget is 0 VND. The user has authorized Q3-A to use their existing
Colab Pro+ credits; no additional subscription, extra-credit purchase or paid API
use is authorized. Journal
fees, active indexing and subject/year-specific quartiles need fresh verification.
Drafted, submitted, accepted and published remain separate milestones.

## Verified engineering outputs

- Public repository and research plans exist.
- The legacy prototype was smoke-tested on the actual **RTX 5050 Laptop GPU
  (8,151 MiB reported by nvidia-smi)**; this machine has no RTX 3060 installed.
- Real seed-0 baseline checkpoints and warm-up logs have been saved to Drive;
  the first evidence archive was independently downloaded and hash-verified.
- No primary hypothesis result, human-evaluation result or editorial outcome has
  been established. The running baselines are not MIM-LM.

Generated PDFs remain local and ignored by Git; version source and QA records.

### Historical three-study preparation — 26 November 2026

The common warm-up retains 3,000/300/300 underlying TinyStories source groups
and adds 2,792/277/280 mechanically derived, same-split three-sentence
instruction examples. No benchmark state labels are added; the 5M-target
cap per initialization is unchanged. General perplexity uses original
held-out stories only. This describes the initial preparation snapshot. Q3-A's
subsequent bounded calibration expands only training sources to 30,000 and adds
conditional continuation examples, preserving the original held-out stories;
see its separate plan and resource/provenance amendment above.

Each study has a Vietnamese briefing with ten difficult advisor questions
and proposed evidence-based answers: [A](docs/Q3_A_BRIEF_AND_ADVISOR_QA.vi.md),
[B](docs/Q3_B_BRIEF_AND_ADVISOR_QA.vi.md),
[C](docs/Q3_C_BRIEF_AND_ADVISOR_QA.vi.md). The current
[verification record](docs/THREE_Q3_PRETRAIN_QA.vi.md) distinguishes completed
engineering checks from deferred optimization and scientific validation.
