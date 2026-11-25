"""Compile the three planned manuscripts and reject broken references/overflow."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = {
    "q3-a": "q3_a_temporal_benchmark",
    "q3-b": "q3_b_state_supervision",
    "q3-c": "q3_c_memory_mechanisms",
}


def main() -> None:
    compiler = shutil.which("tectonic")
    if compiler is None:
        raise SystemExit(
            "Tectonic is unavailable. Install it or use the Codex LaTeX editor."
        )
    report = []
    for short_name, directory in PROJECTS.items():
        project = ROOT / "papers" / directory
        destination = ROOT / "output" / "pdf" / short_name
        destination.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [compiler, "main.tex", "--keep-logs", "--outdir", str(destination)],
            cwd=project,
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
        )
        log_file = destination / "main.log"
        log = (
            log_file.read_text(encoding="utf-8", errors="replace")
            if log_file.exists()
            else ""
        )
        broken = re.findall(
            r"Overfull \\[hv]box|LaTeX Error|Undefined control sequence|"
            r"There were undefined references|Citation .* undefined|Reference .* undefined",
            log,
        )
        pdf = destination / "main.pdf"
        success = result.returncode == 0 and pdf.exists() and not broken
        if success:
            shutil.copyfile(pdf, project / "draft.pdf")
        report.append(
            {
                "project": directory,
                "success": success,
                "compiler_exit_code": result.returncode,
                "pdf": str(pdf.relative_to(ROOT)),
                "bytes": pdf.stat().st_size if pdf.exists() else None,
                "problems": broken,
                "underfull_boxes": len(re.findall(r"Underfull \\[hv]box", log)),
                "console": result.stdout + result.stderr,
                "visual_review": "required separately; successful compilation alone is insufficient",
            }
        )
    path = ROOT / "output" / "pdf" / "build-report.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for item in report:
        print(f"{item['project']}: {'PASS' if item['success'] else 'FAIL'}")
    if not all(item["success"] for item in report):
        raise SystemExit(f"Inspect {path}")


if __name__ == "__main__":
    main()
