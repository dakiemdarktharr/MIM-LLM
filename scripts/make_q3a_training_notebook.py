"""Generate a lightweight private Colab notebook; upload its source bundle separately."""

import argparse
import hashlib
import json
from pathlib import Path

import nbformat as nbf


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bundle", required=True)
    p.add_argument("--registry", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    bundle = Path(args.bundle).read_bytes()
    registry = json.loads(Path(args.registry).read_text())
    plan = json.loads(Path(registry["plans"]["a"]).read_text())
    drive = "/content/drive/MyDrive/MIM-LLM/Q3-A/20261126-" + plan["plan_id"][:12]
    code = nbf.v4.new_code_cell
    md = nbf.v4.new_markdown_cell
    nb = nbf.v4.new_notebook()
    bootstrap = """import hashlib, json, os, subprocess, sys, zipfile
from pathlib import Path
EXPECTED = __SHA__
BUNDLE = Path('/content/source-bundle.zip')
if not BUNDLE.is_file(): BUNDLE = Path(DRIVE)/'inputs/source-bundle.zip'
if not BUNDLE.is_file(): raise FileNotFoundError('Upload source-bundle.zip through the Files pane first.')
blob = BUNDLE.read_bytes()
assert hashlib.sha256(blob).hexdigest() == EXPECTED
ROOT = Path('/content/MIM-Q3A')
ROOT.mkdir(exist_ok=True)
with zipfile.ZipFile(BUNDLE) as archive:
    for item in archive.infolist():
        if not (ROOT/item.filename).resolve().is_relative_to(ROOT.resolve()): raise ValueError('Unsafe path')
    archive.extractall(ROOT)
os.chdir(ROOT)
Path('source-bundle.zip').write_bytes(blob)
saved = Path(DRIVE)/'inputs/source-bundle.zip'
saved.parent.mkdir(parents=True,exist_ok=True)
if saved.exists() and hashlib.sha256(saved.read_bytes()).hexdigest()!=EXPECTED: raise ValueError('A different bundle already exists in this Drive folder')
saved.write_bytes(blob)
assert hashlib.sha256(saved.read_bytes()).hexdigest()==EXPECTED
manifest = json.loads(Path('BUNDLE-MANIFEST.json').read_text())
for name, digest in manifest['files'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
subprocess.run([sys.executable,'-m','pip','install','-q','sentencepiece','pytest'],check=True)
subprocess.run([sys.executable,'-m','pip','install','-q','-e','.','--no-deps'],check=True)
print('Pinned source/data bundle verified:',EXPECTED)
""".replace("__SHA__", repr(hashlib.sha256(bundle).hexdigest()))
    nb.cells = [
        md("""# Q3-A: authorized bounded training

Private execution copy. Scope review: numeric irrelevant-clock control replaces
the older punctuation control. B/C/Q1 training and tokenizer fitting are not
authorized. Use the Pro+ account requested by the user. Never buy extra credits.
Initial GPU session: seed-0 shared warm-ups, soft cap **20 minutes**. Test locked.
Record CU balance/rate in the Colab UI before/after. Mount Drive before training.
"""),
        code(
            """from google.colab import drive
drive.mount('/content/drive')
from pathlib import Path
import json
DRIVE = __DRIVE__
Path(DRIVE).mkdir(parents=True,exist_ok=True)
probe=Path(DRIVE)/'mount-check.json'
probe.write_text(json.dumps({'stage':'before training','persistence':'Drive mounted'}))
assert json.loads(probe.read_text())['stage']=='before training'
print('Persistent destination:',DRIVE)
""".replace("__DRIVE__", repr(drive))
        ),
        code(bootstrap),
        code("""import subprocess,sys
result=subprocess.run([sys.executable,'-m','pytest','-q','-o','addopts=','-m','training','tests/test_q3a_training_integration.py','tests/test_q3a_overfit.py'],capture_output=True,text=True)
print(result.stdout,result.stderr)
(Path(DRIVE)/'engineering-tests.txt').write_text(result.stdout+result.stderr)
assert result.returncode==0,'Stop: optimizer/overfit/resume verification failed'
"""),
        md("""## Training — wait for verified Drive and four passing engineering tests

Select a GPU runtime (prefer T4 initially), then run the bootstrap/mount/test cells
again if Colab starts a fresh VM. This cell runs the complete bounded loop on the
server; shutting down the local PC does not send the next command. Latest/previous
checkpoint copies are hash-verified on Drive after each 120-second chunk. Runtime
failure can still lose work since the last successful sync. CU usage is not
inferred from runtime seconds. No unattended full-matrix launch is embedded.
"""),
        code(
            """import subprocess,sys
PLAN=__PLAN__
cmd=[sys.executable,'-u','scripts/run_q3a_colab.py','--plan',PLAN,'--drive',DRIVE,'--phase','warmup','--wall-seconds','1200']
with (Path(DRIVE)/'warmup-console.log').open('a') as log:
    process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    for line in process.stdout:
        print(line,end='',flush=True);log.write(line);log.flush()
    status=process.wait()
assert status==0,'Run stopped with an error; inspect retained logs/checkpoints'
print('Warm-up session ended. Inspect real validation writing before post-training.')
""".replace("__PLAN__", repr(registry["plans"]["a"]))
        ),
    ]
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python"},
        "colab": {"name": "Q3-A authorized bounded training"},
    }
    nbf.validate(nb)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise FileExistsError(out)
    nbf.write(nb, out)
    print(
        json.dumps(
            {
                "notebook": str(out),
                "bytes": out.stat().st_size,
                "bundle_sha256": hashlib.sha256(bundle).hexdigest(),
                "plan_id": plan["plan_id"],
                "drive_destination": drive,
            }
        )
    )


if __name__ == "__main__":
    main()
