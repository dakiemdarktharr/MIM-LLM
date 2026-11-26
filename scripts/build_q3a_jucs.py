"""Build Q3-A with pinned J.UCS V5 style after real experiments/results complete.

This does not certify submission readiness or replace scientific claim review.
No training, source-corpus access or browser authentication is involved.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from mim_llm.manuscript_workflow import require_results_before_build

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "papers/q3_a_temporal_benchmark"
TEMPLATE_SHA256 = "3506bfc490c87b965c8463db3db5ab71d223d43c703910673158248ecee5b77e"
DEFAULT_TEMPLATE = ROOT / "artifacts/q3a-journal-audit-20261126/jucs-latex-v5.zip"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template-zip", type=Path, default=DEFAULT_TEMPLATE)
    args = parser.parse_args()
    require_results_before_build("q3-a", ROOT)
    if not args.template_zip.is_file() or digest(args.template_zip) != TEMPLATE_SHA256:
        raise SystemExit(
            "Supply the unchanged official V5 ZIP with --template-zip; expected SHA256 "
            + TEMPLATE_SHA256
        )
    compiler = shutil.which("tectonic")
    if not compiler:
        raise SystemExit(
            "Tectonic is unavailable; no alternate font/engine substituted."
        )
    source = (PAPER / "main.tex").read_text(encoding="utf-8")
    start, finish = r"\begin{abstract}", r"\end{abstract}"
    if source.count(start) != 1 or source.count(finish) != 1:
        raise ValueError("Expected one shared manuscript abstract")
    before, rest = source.split(start)
    abstract, body = rest.split(finish)
    title = re.findall(r"\\title\{([^{}]+)\}", before)
    if len(title) != 1 or body.count(r"\end{document}") != 1:
        raise ValueError("Expected one title and document end")
    preamble = (PAPER / "jucs_preamble.tex").read_text(encoding="utf-8")
    header = (
        "\n\\title{{\\fontsize{14pt}{14pt}\\selectfont " + title[0] + "}}\n"
        "\\author{}\n\\date{}\n\\begin{document}\n\\maketitle\n"
        "\\begin{quote}\\small\\textbf{Unsubmitted research draft.} "
        "Compilation requires completed experimental evidence. "
        "Human authorship and final submission declarations still require verification."
        "\\end{quote}\n"
        "\\begin{abstract}\\small\n"
    )
    wrapper = preamble + header + abstract + finish + body
    staging_parent = ROOT / "artifacts/q3a-jucs-build"
    staging_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="build-", dir=staging_parent))
    # Only the style member is read; ZIP paths never become filesystem paths.
    with zipfile.ZipFile(args.template_zip) as archive:
        members = [n for n in archive.namelist() if Path(n).name == "jucs2e.sty"]
        if len(members) != 1:
            raise ValueError("Expected one original publisher style")
        (staging / "jucs2e.sty").write_bytes(archive.read(members[0]))
    inputs = {}
    for path in PAPER.rglob("*.tex"):
        relative = path.relative_to(PAPER)
        destination = staging / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        inputs[relative.as_posix()] = digest(path)
    (staging / "main.tex").write_text(wrapper, encoding="utf-8", newline="\n")
    command = [
        compiler,
        "main.tex",
        "--keep-logs",
        "--keep-intermediates",
        "--reruns",
        "2",
    ]
    completed = subprocess.run(
        command,
        check=False,
        cwd=staging,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    log = (
        (staging / "main.log").read_text(encoding="utf-8", errors="replace")
        if (staging / "main.log").exists()
        else ""
    )
    problems = re.findall(
        r"Overfull \\[hv]box|LaTeX Error|Undefined control sequence|"
        r"There were undefined references|Citation .* undefined|Reference .* undefined|"
        r"Label\(s\) may have changed|"
        r"Missing character:|Font shape .* undefined",
        log,
    )
    pdf = staging / "main.pdf"
    success = completed.returncode == 0 and pdf.is_file() and not problems
    output = ROOT / "output/pdf/q3-a-jucs"
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "success": success,
        "status": "unsubmitted_layout_check_after_experiments_not_final_compliance",
        "engine": subprocess.check_output([compiler, "--version"], text=True).strip(),
        "template_zip_sha256": digest(args.template_zip),
        "original_style_sha256": digest(staging / "jucs2e.sty"),
        "input_tex_sha256": inputs,
        "generated_tex_sha256": digest(staging / "main.tex"),
        "staging": str(staging),
        "pdf_sha256": digest(pdf) if pdf.exists() else None,
        "problems": problems,
        "underfull_boxes": len(re.findall(r"Underfull \\[hv]box", log)),
        "package_warning_lines": re.findall(
            r"^Package .* Warning:.*$", log, re.MULTILINE
        ),
        "deviations": [
            "explicit draft header; no publisher sample metadata",
            "author block empty",
            "keywords/categories and final declarations pending",
            "Tectonic XeTeX rather than recommended LuaLaTeX",
            "unused negative tracking option and ignored geometry width omitted",
            "table cell padding follows the V5 example's 6pt setting",
            "modern enddocument restored after loading legacy publisher style",
        ],
        "visual_review": "required separately for current PDF hash",
        "console": completed.stdout + completed.stderr,
    }
    (output / "build-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    if not success:
        raise SystemExit(
            f"Layout build failed; inspect {staging} and {output / 'build-report.json'}"
        )
    shutil.copyfile(pdf, output / "q3-a-jucs-methods.pdf")
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "success",
                    "staging",
                    "pdf_sha256",
                    "problems",
                    "underfull_boxes",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
