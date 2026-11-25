# Standalone manuscript designs

Four English planning drafts contain independent questions, related work,
methods, result shells and falsification criteria. Author fields are empty.
No program attribution, quartile goal or statement of supporting a future paper
appears in the scientific manuscripts. No result-bearing draft or publication exists.

| Source directory | Current question |
|---|---|
| `q3_a_temporal_benchmark` | Semantic no-op training versus matched lexical controls |
| `q3_b_state_supervision` | Token delay versus intervening semantic updates |
| `q3_c_memory_mechanisms` | Controlled initialization-coupled versus peer roll-in distributions |
| `q1_branch_residual_memory` | Shared-fork residual states versus strong memory-budget controls |

Older directory slugs are retained as stable paths; revision 3 supersedes their
old scopes. Each directory has main.tex, references.tex and a
study_plan.json tracking design and operational preparation separately. Keep the papers/ tree together for shared source inputs.

See [current design](../docs/PORTFOLIO_V3.vi.md),
[novelty audit](../docs/NOVELTY_AUDIT_V3.vi.md) and
[resource manifest](portfolio_v3.json). Shared initialization reuse is disclosed
and counted once in physical compute, rather than fabricated as extra training.

## Build

Run `python scripts/build_papers.py` with Tectonic available. Four PDFs and the
diagnostic JSON are produced in output/pdf/; successful PDFs are copied to local
draft.pdf files. All generated PDFs are Git-ignored. Commit LaTeX/Markdown/JSON
and QA, not generated PDFs. Rendering and claim verification remain separate.
Adopt a verified journal template only when ready to submit.

## Completion gates

All three Q3 studies have preparation code and a [joint handoff](../docs/THREE_Q3_PRETRAIN_RUNBOOK.vi.md).
The [Colab notebook](../notebooks/Three_Q3_Prepare_Colab.ipynb) contains no
executable training or bank-collection cell. Permission blocks model/tokenizer
training. C needs genuine shared warm-up checkpoints and sufficient matched
history overlap before post-training; Q1 remains an architectural design.

Next: authorize bounded optimizer/overfit/resume validation, establish writing
feasibility and actual GPU/CU cost, fix selection/resource limits, train only
declared runs, obtain real blinded judgments and populate actual results.
Naturalistic transfer and novelty remain scientific gates. Disclose shared
artifacts and prior results without republishing them as new. Drafted-with-results,
submitted, accepted and published are tracked separately.
