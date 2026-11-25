# Q3-A independent reader guide

No annotations have been collected. Do not fill a rating from model identity,
reference wording or an automatic parser. Keep PRIVATE-key.jsonl away from readers.

Read the complete prompt, the generated continuation and its mandatory proposition
sheet. Check the holder, action, cabinet state **at the decision time**, and a
sufficient causal reason. Facts supplied for contradiction checking need not all
be mentioned. Distinguish possession from ownership, cancelled plans from completed
transfers, and what the one-time rule actually entails from optional later actions.
Power arriving exactly at the deadline is available. Additional coherent details
and different valid wording are allowed. Check new facts against later sentences.

For each `*_correct`, use 1 if the proposition is correctly conveyed and 0 if
incorrect or omitted. `all_mandatory_correct` is the conjunction of those four
labels. `coverage_fraction` is the fraction of four mandatory propositions
addressed (correctly or incorrectly), so omission and error remain distinct.
Set `contradiction=1` only for a conflict with applicable history, rule consequences
or another assertion; an omission is not automatically a contradiction.

Contradiction types: none, holder, temporal, conditional, cross-world,
self-generated, multiple, other. `none` must agree with contradiction=0.
`format_3_to_5=1` requires three to five intelligible natural sentences; do not
count clock punctuation or initials as sentence boundaries. Rate fluency 1–5:
1 largely uninterpretable; 2 frequent disruptive errors; 3 understandable but
awkward; 4 natural with minor issues; 5 consistently fluent. Fluency is not truth.

Use `unclear=1` for genuinely ambiguous text/evidence; explain it with an evidence
span or omission note. Supply a real reader ID. Discuss no items until both
independent files are saved. Preserve original files and disagreements. Resolve
logical disagreement in an adjudicated file covering the same anonymous items.
Primary analysis retains unclear outcomes as conservative failures, and reports
their count. Never replace unknown labels with confident invented judgments.
