# LaTeX verification: 25 November 2026

The three research-planning documents were compiled with the local bundled Tectonic
engine and inspected as rendered PDF page sheets.

| Project | Pages | TeX exit | Undefined citations/references | Overfull/underfull boxes | Visual review |
| --- | ---: | ---: | ---: | ---: | --- |
| Q3-A temporal benchmark | 5 | 0 | 0 | 0 / 0 | No clipping, overlap, missing glyphs or broken tables seen |
| Q3-B state supervision | 4 | 0 | 0 | 0 / 0 | No clipping, overlap, missing glyphs or broken tables seen |
| Q3-C memory mechanisms | 4 | 0 | 0 | 0 / 0 | No clipping, overlap, missing glyphs or broken tables seen |

The engine prints a nonfatal Fontconfig configuration message on this host.
The TeX font packages render correctly in the inspected PDFs; compilation and PDF
export exit successfully. The complete current logs and machine-readable build
report are retained under output/pdf/ locally and excluded from Git.

Run python scripts/build_papers.py to reproduce the exports. It returns a failure
if a compiler fails, a PDF is absent, citations/references are undefined or boxes
overflow. Each successful PDF is copied beside its main.tex as draft.pdf.

The Codex application compiler did not return a diagnostic result during this
session; the exported PDFs and claims above are based on the completed terminal
Tectonic builds. The built-in editor can still be used for source editing.

All numeric result cells remain empty. Scientific interpretation, data licensing,
independent annotations, institutional approval, actual author contributions and
venue-specific typesetting remain evidence gates. A compiled planning shell is
not a submission-ready scientific manuscript.
