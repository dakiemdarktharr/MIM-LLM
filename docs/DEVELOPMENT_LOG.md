# MIM-LLM development record

Dates use Asia/Ho_Chi_Minh. Entries below summarize verified repository events
and this conversation; the Obsidian vault contains the fuller research notebook.

## 2026-11-26 — Clarified the conversational model objective

- Recorded the user's explicit long-term target: a MIM-based autoregressive
  model capable of complete multi-turn chat, with early ChatGPT-style interaction
  as an aspiration rather than a demonstrated equivalence.
- Persisted the objective in AGENTS.md, README and a capability roadmap covering
  general language pretraining, instruction/chat SFT and multi-turn evaluation.
  Story/logic benchmarks and manuscript milestones remain intermediate evidence.
- Kept the four manuscripts standalone and the three equal training caps intact.
  Updated the Obsidian objective, project overview/roadmap and all four paper logs.
- Documentation only: no model code, training, data, labels or editorial status
  changed. No chat capability or scaling feasibility was established by this update.

## 2026-11-26 — Revision 3: independent studies with equal training caps

- Superseded revision 2's evaluator-only A and architecture-heavy C split.
  All three smaller studies now train four conditions on two backbones with
  three seeds and equal target/selection caps. Pilot post-training is 48M targets
  per study; unique shared warm-up is counted once. Equal GPU-hour caps remain
  unchosen until profiling; rollout/replay costs must be logged separately.
- Rewrote four independent English manuscript shells, including a new candidate
  branch-residual architecture shell. Removed program authorship and statements
  that one paper supports another. Scientific bodies contain no quartile labels
  or target-journal planning. Private integration mapping is kept in Obsidian.
- Completed a new Undermind search: 168 candidate records, not full-text verified
  papers. Retrieved 24 source PDFs and recorded hashes and targeted reading scope;
  one PDF timed out and was screened through its primary metadata/abstract.
  Crossref/OpenAlex screening was small and noisy, not an exhaustive novelty test.
- Added strong threats and corresponding design controls: DTO/CFI, Delayed
  Supervision, StateWise, frozen-learner surprisal/history effects, SEED,
  TreeWY/Flide and NarraWorld. Architectural novelty remains unresolved; simple
  low-rank state, prefix sharing, self-training or gates cannot be claimed as new.
- Instantiated planning backbones: minGRU 2,081,384 and Transformer 2,074,320
  parameters. These configurations were not trained/profiled. The new residual
  architecture is unimplemented with unknown actual parameter count.
- Updated protocol metadata only; `match_width` and model/training/evaluator
  implementations are unchanged. The paper-tracks CLI passed. Four LaTeX builds
  passed without warnings/undefined references/overflow; rendered and inspected
  all 16 pages. Verified 24 source hashes, budget arithmetic and standalone content.
- Updated the Obsidian project to 50 notes/141 resolved wikilinks, preserving
  historical entries and adding explicit corrections, four study plans, novelty
  audit and a private integration map. Journals remain conditional candidates;
  no fresh full fee/quartile/funding approval was established.
- No new model training, human labels, scientific result, paid compute, submission,
  acceptance or publication occurred. New procedures are not train-ready.
  See [revision-3 QA](PORTFOLIO_V3_QA.vi.md) for verification and limits.

## 2026-11-24

- Initialized the public project and English research-plan README.
- Commit: `ab208dc04c597bbf0484bf5df98692d91680e582`.

## 2026-11-25

- Implemented the small vector MIM-LM, baselines, N/S/M ablations, learned-pair
  control, tokenizer/data pipeline, training/resume and evaluation/annotation tools.
- Verified 50 tests on the observed RTX 5050 Laptop host, including CPU/GPU
  checks, causality, full/stepwise agreement and interrupted training resume.
- Recorded actual reference counts: 1,984,320 byte-token parameters and
  2,081,472 parameters with the tested BPE-512 tokenizer. Scientific quality
  comparisons remain unestablished.
- Research pipeline commit: `53c6228c5067f0100f7dc33612c96b6aef2c2f84`.
- Prepared the four conditional study plans, UEH/journal survey, and three
  English Q3 LaTeX research shells. Exported and inspected 13 PDF pages.
- Planning commit: `c84ddd8a17fb8d30e43f0edb4177672029e43cf4`.
- Short calibration: MIM 20,306 targets / 39.84 train seconds; learned-pair
  20,306 targets / 36.24 seconds. Colab throughput and compute-unit burn
  remain unmeasured; the 500-CU budget examples are hypothetical.
- User confirmed UEH student status without a UEH staff coauthor; funding
  eligibility and approval have not been established.
- At the user's request, removed the three generated PDFs from the tracked
  working tree, retained local copies and LaTeX, and ignored future PDF outputs.
  Earlier commits retain their historical contents.
- Created the Obsidian notebook under
  `D:/notes/vault_1/Projects/MIM-LLM`, with one subfolder per planned paper,
  common methods, dated logs, source snapshots and reusable templates.
- Added project instructions to continue updating the notebook after substantive
  work. All result-bearing manuscript/submission/acceptance/publication
  milestones remain unachieved.

### Q3-A preparation and source audit — 25 November 2026

- Retrieved 17 primary-source PDFs and documented targeted reading depth,
  publication/preprint status, URLs, search boundaries and SHA-256 hashes in
  `Q3_A_SOURCE_LEDGER.vi.md` and `Q3_A_SOURCES.json`. The new Undermind deep
  search did not launch because the free allowance was exhausted.
- Added a Vietnamese research dossier and ten advisor questions with proposed
  answers, required evidence and claims that are not yet justified.
- Narrowed Q3-A to incremental diagnostic value. Counterfactual invariance,
  participant-state revision, self-generated story consistency and sequential
  temporal scope have close precedents; novelty remains to be demonstrated.
- Audited the pilot on base commit
  `68e8344afeca39f339b30c404b4618bca12e9c0c`: fixed time tokens,
  distinct-recipient chains and shared template structure leave shortcuts.
  This session changes documentation/manuscript sources, not benchmark code.
- Clarified rule compliance, one-time temporal evaluation, world/time indices,
  possession versus ownership, self-event evasion and visible-history limitations.
  Proposed no-op controls, writing-capability references and paired-difference
  uncertainty; these extensions have not been implemented or measured here.
- Updated the English README and Q3-A LaTeX shell; expanded shared references.
  `python scripts/build_papers.py` passed for all three manuscripts. Final build:
  6/5/5 pages; no undefined citations/references or overfull/underfull boxes;
  rendered and visually inspected all 16 pages. An initial Fontconfig warning
  was resolved for the verification invocation using the bundled fonts.conf;
  no machine-wide settings changed. Generated PDFs remain ignored and local.
- Created four Q3-A Obsidian notes and updated the overview, experiment plan,
  decisions and dated development records. No human labels, scientific training
  results, submission, acceptance or publication were added.

### Q3-A revision 2 and support for Q1 — 25 November 2026

- Revised Q3-A to an evaluator-validity study with a strong information-matched
  checklist control, unmodified generated prose as the primary sample, paired
  source-clustered balanced-accuracy difference, and controlled errors as diagnostics.
  This is a design revision; the evaluators and revised data schema are not implemented.
- Preserved the user's program: Q3-A supplies validated evaluation, Q3-B supplies
  train-only supervision evidence, and Q3-C supplies mechanism/compute evidence
  for Q1. Require disclosure/citation of shared artifacts and fresh Q1 test sources.
- Removed mandatory 120M-target architecture training from Q3-A's core; retained
  it as a conditional Q1/Q3-C extension. Added a canonical study plan, JSON planning
  manifest and ten updated advisor answers; marked earlier scope as historical.
- Added CheckEval as a close primary baseline source (28-page PDF retrieved;
  relevant methodology/setup read, not reproduced) and screened a 2026 narrative
  consistency survey through the authors' institutional repository.
- Rechecked official journal scope/fee statements. Fresh SCImago and full J.UCS
  submission pages returned HTTP 403; the plan no longer calls this a fresh
  submission-verified fee/rank/template check. No acceptance probability is claimed.
- Updated README, publication plan, status, Q3-A LaTeX and paper-tracks metadata;
  model/training/evaluator implementations are unchanged. CLI paper-tracks ran
  successfully. All three LaTeX builds passed; rendered and inspected 6/5/5 pages.
- Created two current Obsidian notes; appended decisions, plans and support roles
  without deleting earlier records. Checked 25 relative Markdown links, 42 notes
  and 73 wikilinks. Details are in Q3_A_REVISION2_QA.vi.md.
- No new model weights, training, human labels, paid compute, scientific findings,
  submission, acceptance or publication occurred in this revision.
