# Planned Q3 manuscript shells

The three English manuscripts are research plans with explicit missing-evidence fields.
Their aims, experiments, primary metric, empty result tables, interpretation branches,
ethics and independent-contribution gates are drafted. They are not result-bearing drafts
or submissions. The Q1 question and all four budgets are in
[the Vietnamese publication plan](../docs/PUBLICATION_PLAN.vi.md).

- q3_a_temporal_benchmark/main.tex: temporal scope, overwrites and counterfactual invariance.
- q3_b_state_supervision/main.tex: training-only state supervision.
- q3_c_memory_mechanisms/main.tex: N/S/M ablations and resource efficiency.

The projects use shared files in shared/. Keep the entire papers/ tree together.
The neutral article style is deliberate while the target journal remains conditional.
Switch to the verified current journal style at submission. Do not insert an unapproved
funding statement or authors who have not contributed.

## Compile

From D:\MIM:

~~~powershell
python scripts/build_papers.py
~~~

This uses Tectonic, emits the three PDFs and a diagnostic JSON under output/pdf/,
and copies each successful PDF to draft.pdf beside its main.tex source.
PDF build outputs are kept locally and excluded from Git. Commit the LaTeX sources
and verification notes when updating a manuscript shell.
The script rejects compile errors, undefined citations/references and overfull boxes.
It does not verify scientific claims or visual layout. Inspect the rendered pages too.
The Codex app editor can open each main.tex for editing; the terminal build is the
verified export path for this version.

## Before calling a paper complete

1. Finalize and license the source-story data; audit labels and source disjointness.
2. Register the primary contrast, sample precision, selection budget and decoding.
3. Verify the needed benchmark/model extensions; current code is a prototype.
4. Train the declared seeds; preserve immutable run IDs, tokenizer/corpus hashes and costs.
5. Collect real independent human labels in Vietnam if pursuing UEH support, adjudicate
   disagreements, and report agreement before adjudication.
6. Populate the empty tables from checked evidence; rewrite abstract, discussion and
   conclusion to match actual findings, including negative findings.
7. Check distinct contribution, overlap with other MIM-LLM manuscripts, journal policy,
   active indexing, fees, quartile/year/category, authorship and institutional eligibility.
8. Compile and inspect again in the final journal template.

Data and numerical results do not automatically complete the scientific interpretation.
No existing shared test can be repeatedly treated as unseen while choosing a later
architecture. Use a new held-out source tranche or freeze all choices before opening it.
