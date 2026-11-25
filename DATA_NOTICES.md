# Dataset provenance and modification notice

The local preparation bundle includes a subset of **TinyStories**, distributed
by Ronen Eldan and Yuanzhi Li at
[roneneldan/TinyStories](https://huggingface.co/datasets/roneneldan/TinyStories),
pinned to revision `f54c09fd23315a6f9c86f9dc80f725de7d8f9c64`.
The retrieved dataset card identifies **CDLA-Sharing-1.0**. The agreement is
available in its unmodified form at
[Community Data License Agreement — Sharing, Version 1.0](https://cdla.dev/sharing-1-0/)
(checked 26 November 2026). Preserve this provenance and the adjacent manifests
when sharing these data. The project's source code is not relicensed by this notice.

**Files have been changed:** `data/raw/q3a-tinystories.jsonl` is a selected,
deduplicated and split subset, not the full upstream release.
`data/processed/three-q3-shared-warmup.jsonl` additionally contains mechanical
three-sentence instruction transformations derived from those same source groups.
These derived data remain under CDLA-Sharing-1.0. Row fields and adjacent manifests
record source IDs, original/derived variants, revision, transformation and hashes.
No additional commercial, platform or redistribution restriction is imposed here.

The common subset has 3,000/300/300 underlying train/validation/test source groups.
The modified corpus contains another 2,792/277/280 derived format rows in the
corresponding splits. Derived rows are not independent new stories or human labels.
Original held-out stories alone are used for general-text perplexity.

The A/B/C controlled sources are project-generated templates. Their exact-string
semantic checks do not establish naturalistic coverage, human annotation validity
or trained writing quality. No production self/peer history bank is included:
it can be generated only from genuine, completed shared warm-up checkpoints.
