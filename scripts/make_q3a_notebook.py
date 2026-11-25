"""Generate the preparation-only Colab notebook with nbformat."""

from pathlib import Path

import nbformat as nbf


def main():
    nb = nbf.v4.new_notebook()
    md = nbf.v4.new_markdown_cell
    code = nbf.v4.new_code_cell
    nb.cells = [
        md("""# Q3-A â€” preparation only (no training)

This notebook prepares/checks **Learning When a Premise Change Should Not Change a Story**.
It contains **no executable training cell**. Keep the runtime on CPU during preparation.
The user has purchased a $50 Colab plan; the exact SKU, remaining CU and GPU/CU rate
have not been verified. Buying a plan does not authorize training.

Upload the local `three-q3-pretrain.zip` bundle to `/content/` in Colab, or run from
the existing Windows repository. The bundle contains source, fixed data and the
content-addressed plan. It is local; do not publish raw datasets/annotation keys.
"""),
        code("""import os, sys, json, hashlib, zipfile
from pathlib import Path
IS_COLAB = __import__("importlib.util").util.find_spec("google.colab") is not None if __import__("importlib.util").util.find_spec("google") else False
WORKSPACE = Path(os.environ.get("MIM_WORKSPACE", "/content/MIM-LLM" if IS_COLAB else str(Path.cwd())))
BUNDLE = Path("/content/three-q3-pretrain.zip")
if IS_COLAB and not WORKSPACE.exists():
    if not BUNDLE.is_file():
        raise FileNotFoundError("Upload three-q3-pretrain.zip first. No GPU is needed.")
    WORKSPACE.mkdir(parents=True)
    with zipfile.ZipFile(BUNDLE) as archive:
        for info in archive.infolist():
            if not (WORKSPACE / info.filename).resolve().is_relative_to(WORKSPACE.resolve()):
                raise ValueError("Unsafe archive path")
        archive.extractall(WORKSPACE)
if not (WORKSPACE / "pyproject.toml").is_file():
    raise FileNotFoundError("Set MIM_WORKSPACE to the prepared repository.")
os.chdir(WORKSPACE)
manifest = WORKSPACE / "BUNDLE-MANIFEST.json"
if manifest.exists():
    for name, expected in json.loads(manifest.read_text())["files"].items():
        actual = hashlib.sha256((WORKSPACE/name).read_bytes()).hexdigest()
        if actual != expected: raise ValueError(f"Changed bundle file: {name}")
print("Workspace:", WORKSPACE, "| Training is not authorized")"""),
        code("""import subprocess
if IS_COLAB:
    subprocess.run([sys.executable, "-m", "pip", "install", "-e", ".[data]"], check=True)
import torch
from mim_llm.training_gate import POLICY
permission = json.loads(POLICY.read_text())
assert permission["model_training_authorized"] is False
assert permission["tokenizer_fitting_authorized"] is False
print({"torch": torch.__version__, "cuda_available": torch.cuda.is_available(), "optimizer_steps": 0})"""),
        md("""## Verify data and the immutable plan

The UTF-8 byte tokenizer is fixed and is not fitted. The bundle has 6,000 training
source groups, 400 validation groups and 400 locked test groups, plus a pinned
TinyStories subset. This check verifies test integrity, not model test outcomes.
"""),
        code("""from mim_llm.q3a.plan import load_plan
PLAN = Path("artifacts/three-q3-final-20261126/a/plan.json")
plan = load_plan(PLAN)
print({"plan_id": plan["plan_id"], "budget": plan["budget"],
       "parameters": {k: v["actual_parameters"] for k,v in plan["models"].items()},
       "maximum_task_context": plan["maximum_task_context"]})"""),
        md("""## Non-optimizing checks

CPU forward/backward, masking/causality/step/reset checks never call an optimizer.
Timing these checks is not a measurement of training throughput. Parameters must
remain identical. Overfit, optimizer-step and interrupted-training integration tests
are intentionally deferred until the user explicitly requests training.
"""),
        code("""from datetime import datetime, timezone
from mim_llm.q3a.preflight import preflight, compute_budget
SESSION = Path("artifacts/colab-preparation") / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
SESSION.mkdir(parents=True)
report = preflight(PLAN, SESSION/"preflight.json", device="cpu")
assert all(r["optimizer_steps"] == 0 and r["parameters_unchanged"] for r in report["models"])
print({"checks": report["status"], "optimizer_steps": 0, "output": str(SESSION)})
print(compute_budget(PLAN))"""),
        md("""## Stop here and wait for the user

No training command runs in this notebook, including with **Run all**. Do not edit
the permission file or request a GPU to continue without the user's new instruction.

After explicit authorization, the next phase is a bounded optimizer/overfit/resume
validation, hardware/CU calibration and one declared pilot contrast before a full
matrix. Exact run IDs and the measured spending/time limits must be authorized.
Checkpoint outputs should be placed on user-selected persistent storage for Colab;
the VM filesystem is temporary. See `docs/THREE_Q3_PRETRAIN_RUNBOOK.vi.md`.

Results, human labels, naturalistic transfer validation and publication outcomes
have not been produced by these checks.
"""),
    ]
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python"},
        "colab": {"name": "Q3-A preparation only"},
    }
    nbf.validate(nb)
    out = Path("notebooks/Q3_A_Prepare_Colab.ipynb")
    out.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, out)
    print(out)


if __name__ == "__main__":
    main()
