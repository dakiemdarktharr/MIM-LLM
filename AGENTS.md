# MIM-LLM project workflow

## LaTeX phase order — user instruction, 2026-11-26

Do not compile any paper's LaTeX until its real data collection, training,
evaluation/test and result analysis phases are complete and actual results exist.
This supersedes earlier preparation-stage compilation instructions. Keep previous
PDF/build receipts as historical local evidence; do not rerun them to polish a
planning draft. Both build scripts enforce the evidence gate documented in
`docs/MANUSCRIPT_PHASE_ORDER.vi.md`. No new permission request is required after
the scientific prerequisites are genuinely complete; do not fabricate receipts.

## Q3-A training authorization — 2026-11-26

The user explicitly lifted the training hold for Q3-A on their Colab Pro+
account, after reviewing all four scopes, with metrics/checkpoints saved to Drive.
Authorized engineering optimizer/overfit/resume checks precede real runs.
Keep exact plan/run IDs in configs/training_permission.json; no tokenizer fit,
B/C/Q1 training, new paid subscription or extra-CU purchase is authorized.
Initial remote GPU session has a 20-minute soft wall cap and seed-0 warm-up
feasibility gate before wider post-training. Preserve shared initialization.
C histories still require genuine shared checkpoints and its grammar-constrained
bank must not be called free authorship. The earlier hold and zero-update
preparation receipts remain historical evidence, not current authorization.

## Long-term model objective

The user's explicit objective, clarified on 2026-11-26, is a MIM-based
autoregressive language model capable of complete, natural multi-turn chat,
with early ChatGPT-style conversation as an aspirational reference. Story
continuation and state-tracking tasks are early research instruments, not the
final capability target. Do not substitute benchmark success or four papers
for building and evaluating a conversational model.

Keep general language learning, instruction/chat fine-tuning and multi-turn
evaluation in the technical roadmap. Track conversational usefulness separately
from memory/logic and publication milestones. Do not claim ChatGPT equivalence,
general chat readiness or feasible scaling from small-model smoke tests.
The four manuscripts remain standalone; put their internal relationship in
project planning, not statements that one manuscript serves another.
See `docs/PROJECT_OBJECTIVE.vi.md` for the capability and evidence gates.

## Development record

The user requested a continuing Obsidian record of this project's development.
The current vault project directory is:

`D:/notes/vault_1/Projects/MIM-LLM`

After substantive research, implementation, experiments, manuscript work, or
publication-policy changes:

1. Append a dated entry to the appropriate note in `07-Logs` and the affected
   paper's `Development-Log.md`.
2. Update the affected experiment plan, overview, or milestone note when facts
   change. Preserve earlier entries and identify corrections explicitly.
3. Record sources, commands/run IDs, actual parameter counts, hashes, verification,
   decisions, limitations, and next work. Distinguish measurements from proposals.
4. Track manuscript drafted, submitted, accepted, and published separately.
   Research shells and smoke tests do not establish those milestones.
5. Record material public-project changes in `docs/DEVELOPMENT_LOG.md` as well.
   Keep unrelated/private vault notes out of the GitHub repository.

If the vault is unavailable, preserve the update in the repository development
log and report that the Obsidian update remains pending.

## PDF policy

Keep generated PDFs local. They are ignored by Git; version the LaTeX sources,
build script, and verification notes. Do not rewrite public Git history unless
the user explicitly requests history removal.

## Research integrity

Use measured hardware and throughput. Colab performance, credit burn, journal
quartile and funding are not established until checked for the actual setting.
Never invent human labels, positive findings, funding approval or editorial
outcomes. Preserve the stop/merge conditions for the four conditional studies.
