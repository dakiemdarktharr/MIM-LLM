# MIM-LLM development record

Dates use Asia/Ho_Chi_Minh. Entries below summarize verified repository events
and this conversation; the Obsidian vault contains the fuller research notebook.

## 2026-11-26 — Q3-A preparation with an explicit training hold

- User reports purchasing a $50 Colab plan and explicitly requires waiting before
  any training. Added a fail-closed model/tokenizer permission policy with exact
  run/plan IDs, including legacy training functions. No runtime was started in Colab.
- Implemented Q3-A controlled pairs and four training arms, response-only CE,
  train-only invariant-probe JS, exact target accounting, immutable input/code
  plans, atomic checkpoints/resume, free generation, test-selection/registration
  gates, blank blinded-reader packets, adjudication and source-paired analysis.
- Added eval-only Transformer KV reuse, checked against full/chunked/padded
  forward on CPU/CUDA, with unchanged parameterization. Suppressed BOS/PAD sampling.
- Prepared final 6,000/400/400 controlled source groups and a pinned 3,000/300/300
  TinyStories subset. Fixed a duplicate-source draw issue before any training;
  earlier preparation artifacts are superseded. Naturalistic transfer is not validated.
- Operational fixed-byte/context-2048 backbones are minGRU 2,099,864 and
  Transformer 2,119,408 actual parameters, replacing earlier Q3-A counting examples.
  Physical warm-up reuse may only be credited when identical checkpoints are used.
- 93 tests passed; six training/fitting cases were deselected, including two
  newly written Q3-A optimizer/JS/interruption-resume integration cases. Real-config
  CPU/CUDA preflight left every parameter unchanged with zero optimizer steps.
  Optimizer/overfit/training-resume integration remains intentionally unexecuted.
- Validated and executed all four preparation-notebook code cells locally on CPU;
  not a Colab execution claim. Exported and round-trip verified a local preparation
  bundle. No training cell is executable in the notebook. Raw datasets, ZIP and
  generated PDFs remain local/Git-ignored.
- Expanded the standalone English methods draft; all four TeX builds passed and
  all five updated Q3-A pages were rendered/inspected. No trained results or real
  labels were inserted. Updated Obsidian and preserved prior records/milestones.
  See [pretraining QA](Q3_A_PRETRAIN_QA.vi.md) and [handoff](Q3_A_PRETRAIN_RUNBOOK.vi.md).

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


### Three-study preparation: B/C implementation and A review — 26 November 2026

- Completed separate B/C data, objectives, guarded post-training/resume engines,
  inference, blind-label analysis and result-table export. B uses disposable QA
  prefixes and exact lag/write checks; C includes genuine frozen-checkpoint
  grammar sampling, provenance verification, matching/sealing and raw-ID
  unconstrained two-stage evaluation. No production C bank or new weights exist.
- Corrected A2 to a byte/edit-count-matched punctuation control, not a full
  paraphrase. Closed A's decision timeline, counterbalanced B0 window selection,
  and cut B evaluation at the high window before later target revisions. C's
  updated title/claim concern controlled roll-in distributions, not intrinsic
  origin identity; known-holder grammar scaffolding is explicitly train-time.
- All three use byte259/context2048: minGRU 2,099,864 and Transformer 2,119,408
  parameters. Shared warm-up keeps 3,000/300/300 TinyStories source groups and
  adds 2,792/277/280 same-split general-format examples; no benchmark state labels.
  General perplexity uses original held-out stories only. Dataset modification
  and upstream CDLA-Sharing-1.0 notices are retained in DATA_NOTICES.md/manifests.
- Prepared equal 48M post-target and 7.2M selection caps per study, six shared
  5M-target initializations counted once, and a 78-job dependency graph. Total
  with full selection reserve: 195.6M targets, zero executed. Equal targets are
  not equal compute. Actual training throughput, Colab GPU/CU burn and spending
  limits are unmeasured. C collection/matching requires real completed warm-ups.
- Ran 131 tests successfully; 10 optimizer/fitting tests deliberately deselected.
  CPU/CUDA preflights and dense [2,2048,259] CE graphs had finite gradients and
  unchanged parameters. Local hardware: RTX 5050 Laptop, not RTX 3060. These
  forward/backward checks are not training throughput or optimizer validation.
- Executed both preparation-only notebooks locally: four code cells each, no
  errors/optimizer updates. Colab remote runtime has not been tested. Created a
  portable local hash-manifest bundle; raw data, ZIP, PDFs, weights and private
  vault notes stay outside Git. Production permission flags/ID lists stay closed.
- Compiled all four LaTeX methods/planning drafts. Fixed a citation key and a
  shared-methods overflow; final builds have no undefined citations/references,
  overfull or underfull boxes. Rendered and visually reviewed all 14 A/B/C pages
  (5/4/5). Authors and result fields remain empty; generated PDFs remain local.
- Wrote independent Vietnamese task/method briefs with ten advisor questions
  and proposed answers per Q3. Updated Obsidian's shared/paper overviews, plans,
  milestones, decisions and development logs, preserving earlier entries.
- Checked relevant primary preprints Delayed Supervision (2609.32312), StateWise
  (2610.33766) and Enaction (2605.25459); this is not an exhaustive new novelty
  clearance. No new quartile/funding/fee check, human labels, result-bearing
  manuscript, submission, acceptance or publication occurred. Transfer beyond
  templates and finite C support, writing feasibility and novelty remain gates.
- Source baseline: 36eaa65bedb7d6474784c7e12f6c53a8bf271cc7. Current plan IDs and
  receipts are recorded in THREE_Q3_PRETRAIN_QA.vi.md and prepared snapshots.
  Policy requires a new user training instruction before optimizer/overfit/resume
  tests or training. Long-term complete MIM-based chat remains unestablished.

- Added a B/C annotation rubric and beginner terminology guide; it requires real validation readers before freezing, and contains no collected human judgments.


## 2026-11-26 — Scope review and Q3-A Colab launch preparation

User explicitly authorized Q3-A training on the confirmed Pro+ account and Drive persistence. B/C/Q1 and tokenizer fitting remain closed. A2 replaces historical punctuation edits with a decision-irrelevant numeric clock: independent time, same byte/edit count; A1 is decision-preserving variation of the relevant power time. No claim of pure semantic causality or acceptance probability.

Read primary task/method sections for DTO, Counterfactual Invariance, Delayed Supervision and Enaction; primary abstract/metadata for StateWise, SEED and Flide. Reused completed Undermind25Nov search as candidate evidence, not a new exhaustive search. C's nine grammar forms remain a feasibility pilot; independent-paper claim requires transfer/insight. Q1's compression+forking novelty remains unresolved.

Added step UTC/objective/CE/JS/LR/gradient/token/cursor/time/VRAM logging, validation CE/PPL/corpus/denominator records, environment/software/GPU receipts and checkpoint SHA. Separated regular checkpoint100updates from validation500updates and final. Preserve replayed training and validation work. Driver verifies initial zero-update checkpoint on Drive before any updates, then latest/previous copies after120second chunks. No global atomic-transaction claim for Drive rename. Initial cloud soft cap20min, seed0 shared warm-ups only, before writing/compute feasibility and matched A1/A2 post runs.

Checks:133non-training tests pass;4authorized optimizer/JS/resume/memorization tests pass. Their fictional unit fixtures are engineering evidence, not trained scientific findings. All4LaTeX builds pass. Initial6.4MB notebook upload succeeded but its embedded source caused UI timeouts; closed that browser tab and changed generator to a lightweight notebook plus separate bundle. CPU bootstrap may have been requested; no cloud GPU/warm-up/checkpoint has been verified at this log point.

Current plan: `ba881daafbbd3334ba7c8b7f437415ec3f196e09ee921f5135022375c825f142`; max context1,748 tokens; models2,099,864/2,119,408 parameters. Registry artifacts/q3a-cloud-20261126/registry.json, controlled data data/processed/q3a-launch-20261126. Prior fingerprints/IDs stay historical, not resumed. Local tokenizer fitting remains false.

See docs/SCOPE_REVIEW_BEFORE_TRAIN_20261126.vi.md. Drafted-with-results/submitted/accepted/published remain unachieved. Actual cloud runtime, CU burn, scientific metrics and Drive verification will be appended only after observed.


## 2026-11-26 — Active goal through Q3-A manuscript and evidence QA

Explicit user goal: complete Q3-A training, real analysis/manuscript, prior-literature comparison and a journal-specific quality audit. No acceptance/quartile guarantee; no fabricated labels or positive findings; no extra-CU purchase or B/C/Q1 training. Goal remains active until evidence gates genuinely complete or stop/merge is resolved.

Light notebook now created in the confirmed Pro+ account: private notebook URL retained in local/vault receipts . CPU runtime connected; source-bundle.zip upload visible. First execute request during allocation failed with fetch error; after backend connection, Drive-mount cell ran to an explicit access prompt. No cloud GPU/warm-up/Drive checkpoint verified yet. A manual Google Drive permission step is pending. No new request for training permission is needed.

Bundle SHA2562ad7e8d63189ffc84b5802cf31df01950d596bc2d57021a56f8f9e7240ac6f2b; plan ba881daafbbd3334ba7c8b7f437415ec3f196e09ee921f5135022375c825f142. All4LaTeX builds pass, updated A5pages visually inspected. Current goal/evidence gates: docs/Q3_A_ACTIVE_GOAL.vi.md.
