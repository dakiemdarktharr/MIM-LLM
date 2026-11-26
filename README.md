> **Current execution, 27 November 2026:** Driver 12 is independently audited: minGRU **3,682,887 parameters** completed 80M LM targets and **12,248,567 / 20M SFT targets**. Transformer **3,681,984 parameters** retains its completed 100M parent. All 137 archive members, 383,658 step rows and the numerical contract were verified. The full SFT driver measured 11,776.03 response targets per optimizer second; this excludes I/O and review. **Driver 13 is running**, session `20261126T212456Z`, with the same T4/Drive mount and caps. Negative Transformer retention remains recorded. See the [driver 12 audit](docs/Q3_A_FOUNDATION_INVOCATION12_20261127.vi.md). Writing review, human evaluation, post-training, test, transfer evaluation and a results manuscript remain incomplete; LaTeX is gated. Neither baseline is MIM; B/C/Q1 training and tokenizer fitting remain closed.

> **Historical byte calibration:** Each baseline completed 50M supervised byte targets, but review of all 34 fixed samples failed writing/prefix-conditioning feasibility. Its final Drive archive was independently verified (53 files, 81,262 step rows), and that earlier VM was released. The failures remain in the [calibration report](docs/Q3_A_CALIBRATION2_RESULTS_20261126.vi.md). Changing corpus, tokenizer and model configuration together is a feasibility revision, not an isolated causal test of tokenization or a positive architectural result. Further matrix expansion still requires writing review.

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

1. **Learning When Premise Changes Preserve Narrative Consequences:** semantic no-op
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
Q3-A's prepared byte pipeline implements paired response training, invariant-probe
JS, checkpointing, generation, blank blind annotation and source-paired analysis.
The current subword extension has foundation training, compatible CE/JS helpers,
a fixed writing-review exporter and a blank author-reader packet tool. Its
primary post-training runner/plan and evaluation migration are not yet complete;
passing foundation or software checks does not release that matrix. The
available reader is currently the author alone; no independent-reader agreement
or human ratings are claimed. B/C's prepared byte pipelines do not automatically
accept the new subword parents.
An [offline external-reference diagnostic](docs/Q3_A_REFERENCE_DIAGNOSTIC_20261126.vi.md)
also counted the published TinyStories-1M checkpoint at **3,745,984** actual
parameters and retained 32 samples. It is not a matched-data/compute comparison
or evidence that our models pass the writing gate.
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

### Historical three-study preparation â€” 26 November 2026

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
