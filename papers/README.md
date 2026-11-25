# Standalone manuscript designs

Four English planning drafts contain independent questions, related work,
methods, result shells and falsification criteria. Author fields are empty.
No program attribution, quartile goal or statement of supporting a future paper
appears in the scientific manuscripts. No result-bearing draft or publication exists.

| Source directory | Current question |
|---|---|
| `q3_a_temporal_benchmark` | Semantic no-op training versus matched lexical controls |
| `q3_b_state_supervision` | Token delay versus intervening semantic updates |
| `q3_c_memory_mechanisms` | Frozen self-origin versus peer-origin history provenance |
| `q1_branch_residual_memory` | Shared-fork residual states versus strong memory-budget controls |

Older directory slugs are retained as stable paths; revision 3 supersedes their
old scopes. Each directory has main.tex, references.tex and design-only
study_plan.json. Keep the papers/ tree together for shared source inputs.

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

Q3-A has preparation code and a [pretraining handoff](../docs/Q3_A_PRETRAIN_RUNBOOK.vi.md).
Its [Colab notebook](../notebooks/Q3_A_Prepare_Colab.ipynb) contains no executable
training cell. The current permission policy blocks model and tokenizer training.
Other revised study procedures remain implementation work.

Implement and test the new data/objective/history/architecture procedures; audit
licenses, source splits and labels; establish writing feasibility; preregister
contrasts and budgets; lock tests; train declared seeds; collect genuine blinded
human judgments; report negatives/unclear cases; and populate results from actual
logs. Disclose shared artifacts and prior results without republishing them as
new. Drafted/submitted/accepted/published are tracked separately.
