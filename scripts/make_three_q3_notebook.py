"""Create a CPU preparation notebook; no executable training or bank-collection cell."""

from pathlib import Path

import nbformat as nbf


def main():
    nb = nbf.v4.new_notebook()
    md = nbf.v4.new_markdown_cell
    code = nbf.v4.new_code_cell
    nb.cells = [
        md("""# Three independent studies — preparation only

Keep the Colab runtime on **CPU**. Upload the local `three-q3-pretrain.zip` to
`/content/`. This notebook verifies code/data and runs non-optimizing checks.
**Run all cannot train a model or fit a tokenizer.** The $50 subscription is
user-reported; GPU/CU rates, remaining credits and training time are unmeasured.
"""),
        code("""import os, sys, json, hashlib, zipfile
from pathlib import Path
try:
    import google.colab
    IS_COLAB = True
except ImportError:
    IS_COLAB = False
WORKSPACE = Path(os.environ.get("MIM_WORKSPACE", "/content/MIM-LLM" if IS_COLAB else str(Path.cwd())))
BUNDLE = Path("/content/three-q3-pretrain.zip")
if IS_COLAB and not WORKSPACE.exists():
    if not BUNDLE.is_file(): raise FileNotFoundError("Upload three-q3-pretrain.zip first; no GPU needed.")
    WORKSPACE.mkdir(parents=True)
    with zipfile.ZipFile(BUNDLE) as archive:
        for item in archive.infolist():
            if not (WORKSPACE/item.filename).resolve().is_relative_to(WORKSPACE.resolve()):
                raise ValueError("Unsafe archive path")
        archive.extractall(WORKSPACE)
if not (WORKSPACE/"pyproject.toml").is_file(): raise FileNotFoundError("Set MIM_WORKSPACE to the prepared repository.")
os.chdir(WORKSPACE)
if (WORKSPACE/"BUNDLE-MANIFEST.json").exists():
    for name, expected in json.loads((WORKSPACE/"BUNDLE-MANIFEST.json").read_text())["files"].items():
        if hashlib.sha256((WORKSPACE/name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Changed bundle member: {name}")
print("Workspace verified:", WORKSPACE)"""),
        code("""import subprocess
if IS_COLAB:
    subprocess.run([sys.executable,"-m","pip","install","-e",".[data]"],check=True)
from mim_llm.training_gate import POLICY
policy=json.loads(POLICY.read_text())
assert not policy["model_training_authorized"] and not policy["tokenizer_fitting_authorized"]
assert not policy["authorized_run_ids"] and not policy["authorized_plan_ids"]
print("Training permission is closed; zero optimizer steps.")"""),
        md("""## Verify the three plans and shared initialization dependency

A2 is a byte/edit-matched punctuation control, not a semantic paraphrase.
B keeps event-language data unchanged across schedules; QA uses disposable prefixes.
C training roll-ins are explicitly grammar-constrained; main evaluation is free.
**No production self/peer history bank exists before genuine warm-up checkpoints.**
"""),
        code("""from mim_llm.q3a.plan import load_plan as load_a
from mim_llm.q3bc.plan import load_plan as load_bc
REGISTRY=Path("artifacts/three-q3-final-20261126/registry.json")
registry=json.loads(REGISTRY.read_text())
plans={s:(load_a(path) if s=="a" else load_bc(path)) for s,path in registry["plans"].items()}
for s,p in plans.items():
    print(s.upper(),p["plan_id"],{k:v["actual_parameters"] for k,v in p["models"].items()})
assert len(registry["job_graph"])==78
print("Planned: six shared warm-ups, 24 post-training runs per study. None executed.")
print("C bank pending:",plans["c"]["sealed_bank"] is None)"""),
        md("""## CPU forward/backward checks without optimizer updates

For C, these are explicitly teacher-controlled tensor fixtures. They do not
stand in for self/peer training data and do not establish free-writing quality.
Timings here are not training throughput or a Colab cost estimate.
"""),
        code("""from datetime import datetime, timezone
from mim_llm.q3a.preflight import preflight as preflight_a
from mim_llm.q3bc.preflight import preflight as preflight_bc
session=Path("artifacts/preparation-session")/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
session.mkdir(parents=True)
for s,path in registry["plans"].items():
    report=(preflight_a(path,session/f"{s}.json",device="cpu") if s=="a" else preflight_bc(path,session/f"{s}.json",device="cpu"))
    checks=report["models"] if s=="a" else report["checks"]
    assert all(x["optimizer_steps"]==0 and x["parameters_unchanged"] for x in checks)
    print(s.upper(),"non-optimizing checks passed")
print("STOP: wait for the user's new training instruction.")"""),
        md("""## Authorized future stages — not executed here

1. Bounded optimizer/overfit/resume checks, then writing feasibility and actual GPU/CU calibration.
2. Reuse each of the six declared initialization checkpoints; do not pretrain separately per paper.
3. Collect C's genuine frozen-model histories, match/seal them, stop on insufficient overlap, then bind its immutable execution plan.
4. Schedule A/B/C post-training under equal declared caps. Log B replay and C collection/NLL costs separately.
5. Validation selection, fixed registration/source samples, then test generation and real independent readers.

No permission file is edited here. No training cell, paid API, runtime allocation
or automatic bank generation exists in this notebook. Use persistent storage
for checkpoints only after the user authorizes training. See
`docs/THREE_Q3_PRETRAIN_RUNBOOK.vi.md` and each paper's advisor brief.
"""),
    ]
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python"},
        "colab": {"name": "Three Q3 preparation only"},
    }
    nbf.validate(nb)
    out = Path("notebooks/Three_Q3_Prepare_Colab.ipynb")
    out.parent.mkdir(exist_ok=True)
    nbf.write(nb, out)
    print(out)


if __name__ == "__main__":
    main()
