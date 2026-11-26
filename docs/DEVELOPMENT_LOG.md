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


## 2026-11-26 — Journal and annotation evidence while Drive handoff is pending

No browser calls were made while user takeover remained pending. Goal stays active; no new cloud training/Drive verification is claimed. Meaningful independent progress: J.UCS SJR2025 0.308/Q3 Computer Science(miscellaneous), rank216/403, read from SCImago primary record via indexed results; direct reader403 recorded. Publisher about page fetched through a normal public GET200 and its fee/author/AI/review/license requirements inspected. DOAJ API corroborates no APC/no other charges and current CC BY4.0, resolving stale indexed CC BY-ND metadata. JCR/current active Scopus/WoS coverage not independently verified; no claim of acceptance probability or funding approval.

J.UCS V5 template and V6_2026 publishing agreement downloaded/hashes logged locally; nothing signed/submitted. StyleGuideV4 PDF403 recorded. Crossref metadata confirmed two scope precedents (10.3897/jucs.118889 and10.3897/jucs.137103); do not treat metadata as full-text review. IA's own metrics page now reports JIF2025 Q4 versus2024 Q2; cannot call it a freshly verified Q3 backup.

Calculated real matrix annotation load:24post runs,12primary runs,3roles,1decode seed. At an ASSUMED2minutes/output/reader and2readers,24sources need57.6reader-hours for primary,115.2for all arms;400sources need960/1920hours. Not measured annotation times or power estimates. Pilot readers/precision/source sampling must precede final test; no fake human labels.

Created16-requirement evidence board and AI-use ledger. Product version OpenAI.Codex26.1120.6357.0 verified via local package metadata; model ID unrecorded, not invented. Source inspection flagged A coverage/fluency aggregation using readerA when no adjudication. Frozen training bundle unchanged; a versioned analysis correction and tests are required before real-label analysis. No manipulation of human ratings or silent checkpoint provenance changes.

Files: docs/Q3_A_JOURNAL_VERIFICATION_20261126.vi.md; docs/Q3_A_ANNOTATION_FEASIBILITY.vi.md; configs/q3a/evidence_gates.json; docs/Q3_A_AI_ASSISTANCE_LEDGER.json; scripts/plan_q3a_annotation_load.py. Receipts: artifacts/q3a-journal-audit-20261126. Publication/training milestones remain incomplete.


## 2026-11-26 — Versioned Q3-A analysis correction before real labels

Added q3a-reviewed-quality-1 outside the frozen training fingerprint set. Coverage/fluency average both independent readers itemwise unless an explicit full adjudication file is supplied. Primary judgments/bootstrap are unchanged; unresolved logical/format disagreements still block primary results. Complete source × role × training seed × decoding seed × backbone × predeclared-arm panels are enforced, including cases missing in both primary arms at one seed. Raw generation/key identity, original token bytes, prompt/facts/world/scenario/pair metadata, exact plan/run declarations and final-test selection are checked. Invalid text stays in the denominator; clean_utf8_fraction is a secondary writing metric, not a new machine primary gate.

Added analysis/source/quality-rule/test-arm fields to the draft registration template; its unfilled effect/resource/sample/hash fields remain draft. Updated current runbook's historical training-hold wording: four authorized engineering optimizer/overfit/resume checks already passed, but scientific training has not been observed. Old analyzer retained for frozen provenance; new analysis CLI is documented separately.

Verification:15 new fictional UNIT-fixture tests passed, full default suite148passed/12deselected; Ruff checks/format passed for new code/tests. Tests cover the CLI with a mocked plan loader, plus source tampering, test lock, missing panels, two readers/adjudication and invalid bytes; existing suite and a separate real-plan load verify the loader/data/fingerprint contract. No new optimizer run, real human labels or model findings. Plan ba881daafbbd3334ba7c8b7f437415ec3f196e09ee921f5135022375c825f142 and source ZIP SHA2562ad7e8d63189ffc84b5802cf31df01950d596bc2d57021a56f8f9e7240ac6f2b reverified unchanged. Analysis normalized-source SHA2560d35e6789f64f99ebc355a4943d7697105f6761c777417740a33a0bff3bf380c.

Commands: python -m pytest -q; python -m ruff check/format on the two new files; load_plan(current plan), sha256(current ZIP), source_sha256(new analyzer). No browser calls during pending manual Drive handoff. No cloud optimizer/metric/checkpoint progress inferred. Goal remains active and scientific/manuscript/publication gates remain incomplete. Updated docs/Q3_A_ANALYSIS_REVIEW.vi.md, evidence board and Obsidian records.


## 2026-11-26 — External transfer source audit, not an accepted test set

Checked three specific official-source candidates using their papers, author repositories and official cards: Natural Stories, ProPara and TRIP. Natural Stories pinned4700daad696e942f5aba23c957a7423d0de66612: corpus LICENSE is CC BY-NC-SA4.0; author-edited narratives target rare syntax, not a random sample of natural stories. Saved only LICENSE/README/words.tsv locally, no participant reading-time data. Pinned words.tsv SHA2560955415234babe7fe6890e447d96a2520175f5ea2b8eb130bd31e6aea94e4495. Parsed10stories,10256`.whole` units (not paper lexical words/LM byte tokens), checked unique contiguous positions. Reconstructed text lengths5209–6538UTF8bytes: all exceed2048byte-token context as full stories. Excerpt construction needs self-contained premises and generation reserve checks; every window remains nested in its parent story for splits/uncertainty. No human semantic audits or accepted intervention pairs.

ProPara paper describes488human-authored procedural paragraphs; repository Apache2.0 identified but external package terms not fully cross-checked, and procedural state prediction does not itself evaluate story continuation. TRIP official card has license:[]; no root license in inspected repo listing. Recorded both as conditional component/transfer candidates, not imported test corpora or newly established primary baselines. Correct TRIP paper verified from the official card: ACL2021.findings-emnlp.422 (not other guessed ACL numbers opened during discovery).

Created configs/q3a/transfer_sources.candidates.json and docs/Q3_A_TRANSFER_SOURCE_AUDIT_20261126.vi.md. Current holder/action/cabinet/reason annotation schema is not general enough for arbitrary stories; a generic obligation schema and real two-reader semantic task audit remain necessary. Do not call inserting cabinet templates into other prose naturalistic transfer or count hundreds of windows as independent sources. Candidate manifest is not a final test registration. Source files/license hashes rechecked, JSON parsed, zero accepted pairs retained. No new training, tokenizer fitting, fabricated human labels or corpus publication; frozen training bundle untouched. Manual Drive takeover still pending, with no browser calls or cloud progress assumed.

Reviewed current methods manuscript and official J.UCS V5 readme: current generic article layout is a planning draft; publisher styling/final result-bearing PDF QA remains a separate gate. Existing compiled planning PDFs do not establish final journal compliance.


## 2026-11-26 — User changed phase order: no more LaTeX compilation before results

Explicit new instruction: finish each paper's real data collection, training, evaluation/test and result analysis before compiling LaTeX. Applies independently per manuscript; no new approval is required once those actual scientific prerequisites are met. Updated AGENTS, current runbook notices, docs/MANUSCRIPT_PHASE_ORDER.vi.md and the evidence board. Earlier planning-build directions are historical, not current permission. No TeX process was launched after this instruction.

Implemented require_results_before_build in both build entrypoints, before compiler discovery/invocation. It requires a paper-specific local scientific-readiness receipt, every phase marked complete, and existing evidence files with matching SHA256; no early-draft bypass flag. Identity hashes/flags alone are not proof of scientific validity: real run/data/labels/test/results audits must precede creating receipts. No production readiness receipt exists. Five fictional unit tests check missing results/phases, changed artifacts and both entrypoints stopping before compiler access. Full default suite153passed/12deselected; Ruff passed. No new optimizer tests or training. Frozen training plan and ZIP hashes reverified unchanged.

Prior to the new instruction, generic four-draft compilation passed and an unsubmitted six-page J.UCS V5 layout was rendered/reviewed. Original publisher style SHA2560ce94d0f9455bb9dbc97e0ac813df5b68ea5d9a204e91b5c01d794046ab612e2, official ZIP3506bfc490c87b965c8463db3db5ab71d223d43c703910673158248ecee5b77e; historical PDF0cfefae5f01aba9062236c529180e6315ba594faee48b996129948b1dc8314b2. Fixed long revision overflow, table padding and legacy enddocument compatibility, with no undefined refs/citations, clipping or overlap observed. Six underfull and three package warnings plus a Fontconfig diagnostic remained disclosed. Times New Roman fonts were embedded; pypdf7.1.1 confirmed actual parameter counts and absence of publisher sample names/dates. These are historical layout checks, not results/manuscript-completion evidence. The current source/header/build-lock edits have deliberately NOT been compiled again. PDFs/fonts/publisher ZIP/style remain local and ignored; source and build scripts only are versioned.

Current methods text records reviewed two-reader analysis and actual AI assistance, with human authorship/ethics/declarations still pending. Q3-A remains awaiting manual Drive consent; no browser calls, cloud training, checkpoint or metrics progress inferred. B/C/Q1 training and tokenizer fitting remain unauthorized. Focus returns to the experimental sequence; do not use manuscript formatting as a substitute for real experiments.


## 2026-11-26 — Goal blocked on pending manual Drive handoff

Goal tool returned status BLOCKED after the same Drive-consent/browser-return condition persisted across at least three consecutive goal turns. Independent analysis/source/workflow preparation was completed first. Current audit: clean tree at ecb0a4af21c9cd44cf3076e2bdc7e5e1f859a345 before this status record; no local artifacts/colab-q3a-runs directory and no scientific manuscript-readiness receipts. These local absences do not prove anything about an unobserved remote runtime. No browser calls were made while takeover remained pending; no live cloud training job, remote termination or completed consent is inferred.

This is not completion or a new training-permission request. The full Q3-A objective and existing training authorization remain intact. Need the user's explicit browser return after finishing Google Drive notebook consent; then inspect/verify the mount, source bundle, initial persistent checkpoint and actual GPU/CU before bounded warm-up. Writing feasibility precedes expanding the declared run matrix. Human labels, test analysis, result-bearing writing and final compilation remain future phases. No TeX run, model training, tokenizer fit, new subscription, extra CU purchase, submission or editorial outcome occurred in this status audit. LaTeX stays held under the latest instruction.


## 2026-11-26 — Two real Colab warm-ups persisted; writing feasibility failed

Drive consent resolved and user returned control; goal resumed ACTIVE. T4/PyTorch2.14.1+cu130 completed seed0 Transformer2,119,408 and minGRU2,099,864 shared warm-ups, exactly5,000,000 supervised targets and4,400 updates each. Driver296.443s within chosen600s cap; training seconds85.933/136.837, validation16.067/21.189 respectively. Original general-validation250,090 targets: CE2.144985/PPL8.541913 Transformer and CE1.163324/PPL3.200555 minGRU. Mixed warm-up best CE1.955963/1.073232 uses a different308,953-label corpus. Byte-token PPL is not word PPL. These are baseline models, not MIM architecture results.

Read-only fixed-policy validation inspection saved all6outputs/tokenIDs: minGRU identical across3prompts and all hit512token cap; Transformer samples differ but show substantial word/grammar errors. Human labels remain null; no primary contrast, human quality scores or final-test release. The full post-training matrix was NOT launched. Failure to follow/continue natural prose is a real calibration limitation; it neither establishes nor refutes A1-A2. Trained full/step/causality checks passed in tested scope; T4 full check used cached-eval, with an additional local CPU dense/dropout0-vs-cache check. Different Torch environments and finite checked sequences limit the claim.

After runtime disconnect/deletion, authenticated Drive connector fetched46,329,484-byte evidence archive; independently verified ZIP SHA3e9a2631cd851d873fc9a4917c7fa7857fbe89922f92faf8fb32c38c7303b8fe and27member hashes,8,800ordered finite metric rows and both final checkpoints. Transformer final bff431959d4eeb17707d1b63c61b63fef14fd90a704349879aac75ed0990195a; minGRU final e366ae6e6a26e01af4ee79ba9cef1758c3d26793e5f3b19fd78a356a7e6e7c83. Weights/rawmetrics/ZIP/private cloud URLs stay local/Drive, ignored by Git. No live GPU job now. UI599.49CU before GPU work, last599.25before disconnect, approximate1.24CU/h; final actual debit unknown. Initial allocation observed15:57Vietnam, disconnected before16:15:42; do not equate driver time with billing.

Added scripts/inspect_q3a_warmup.py (actual executed normalized SHA5dea2e8830d1ee00e6a97e5cd649be0c7fe558d6f1a9ff30edc07248f62adb8f), docs/Q3_A_COLAB_PILOT_20261126.vi.md and updated evidence board. Next: one prospectively bounded initialization/data-format repair, preserving old pilot/held-outs/tokenizer/decoding, before further training. No new tokenizer fit, B/C/Q1 training, paid purchase, human labels or LaTeX compilation. The full objective remains incomplete.


## 2026-11-26 — One prospective bounded language calibration prepared

Preserved failed5M-target warm-ups and their entire evidence. New protocol docs/Q3_A_CALIBRATION2_PROTOCOL.vi.md changes two calibration factors together:30,000TinyStories train sources and explicit prefix-to-next3sentence rows, retaining every previous row including300validation/300test unchanged. Added sources only upstream train at the same pinned revision; exact full-text duplicates/protected sources excluded, near-duplicate exclusion not claimed. Mixed counts54,818/612/585; no benchmark state labels or tokenizer fit. Both models freshly seeded0, same259byte tokenizer/architecture/2.10Mactual params/decoding;50Mtargets each, max3x1100s drivers. Cap reservations persist to Drive and unresolved sessions fail closed. No automatic post-training. These joint changes cannot identify which factor improves writing.

Plan ef827ca21a627ce714caaea1d0ab52b293f858e526e654358bbb633c36328660; private bundle2a1628b6a778007a92179742884f6dfec2dba29641f47f5f63b5a92769711522,24,026,393bytes, all member hashes checked. Expanded rawSHA22eb4bb062f6276548fb7c673304ff468f88179a2e43cca004da0015fca8727b; mixedSHAa23917217e47bbb221a525b0cddab6bc8510240a541a23d720eda9fa57992b70. Old plan/ZIP unchanged; post/other-seed IDs removed from current permission file until feasibility review, historical authorization retained in Git. New exact plan and two run IDs recorded. New data3nontraining tests passed, budget2nontraining tests passed; prior full suite156passed/12deselected. No new optimizer yet. More-prefix inspection preselects validation sources3..16 before generation, retaining all output/null human labels.

User reports only themselves currently available as an English reader. No second reader or human labels claimed; this is a future scientific-evaluation dependency, not a blocker for current language calibration. No additional CU/subscription, B/C/Q1 training, final-test release or LaTeX compilation. New calibration is prepared, not yet a measured result. Initial-pilot report committed/pushed f9902947f1eb02c97320ac4e1d22577b19aa3d6d, remote main verified.
