# MIM-LLM development record

Dates use Asia/Ho_Chi_Minh. Entries below summarize verified repository events
and this conversation; the Obsidian vault contains the fuller research notebook.

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
