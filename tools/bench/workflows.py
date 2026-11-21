"""Offline paired benchmark. Run as python -m tools.bench.workflows."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "c49737b01ee679e95320fdb931fc807c7a05c963"
HELPER = ROOT / ".agents/skills/gh-fix-ci/scripts/inspect_pr_checks.py"
CASES = {
    "markReviewed": ("app/index.html:114", "test_demo_review_action_is_present_and_explained"),
    "recordReview": ("api/openapi.yaml:133", "test_api_contract_has_consistent_error_schema_and_review_route"),
    "CI": ("contract-tests", "Validate OpenAPI contract", "ERROR invalid synthetic contract"),
}
# Only these responses are available. Unknown operations fail locally.
FAKE_GH = """#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ['CALLS'], 'a') as f:
    print('gh', file=f)
if args == ['auth', 'status']:
    pass
elif args[:2] == ['pr', 'checks']:
    print(json.dumps([{'name':'contract-tests','state':'FAILURE',
        'detailsUrl':'https://github.com/demo/demo/actions/runs/123/job/456'}]))
elif args[:3] == ['run','view','123'] and '--json' in args:
    print(json.dumps({'name':'Prototype checks','conclusion':'failure'}))
elif args in (['run','view','123','--log'], ['run','view','123','--job','456','--log']):
    print(Path(os.environ['SYNTHETIC_LOG']).read_text())
else:
    sys.exit(2)
"""


def measure(repo, env, task, mode):
    calls = Path(env["CALLS"])
    calls.write_text("")
    outputs = []

    def invoke(*args, expected=0):
        result = subprocess.run(args, cwd=repo, env=env, capture_output=True, text=True)
        if result.returncode != expected:
            raise RuntimeError(f"{Path(args[0]).name} returned {result.returncode}")
        outputs.append(result.stdout)
        return result.stdout

    started = time.perf_counter_ns()
    if task == "CI":
        if mode == "before":
            check = json.loads(invoke("gh", "pr", "checks", "1", "--json", "name,state,detailsUrl"))[0]
            run = check["detailsUrl"].split("/runs/")[1].split("/")[0]
            invoke("gh", "run", "view", run, "--log")
        else:
            invoke(sys.executable, HELPER, "--pr", "1", "--max-lines", "3", "--context", "1", expected=1)
    elif mode == "before":
        found = invoke("git", "grep", "-n", "-F", "-e", task)
        hit = next(line for line in found.splitlines() if line.startswith("tests/"))
        path, number, _ = hit.split(":", 2)
        invoke("sed", "-n", f"{max(1, int(number)-8)},{number}p", path)
    else:
        invoke(sys.executable, ROOT / "tools/codex_context.py", task)
    elapsed = (time.perf_counter_ns() - started) / 1e6
    output = "".join(outputs)
    # Count git/gh via shims, plus the Python or sed command when launched.
    count = len(calls.read_text().splitlines()) + int(mode == "after" or task != "CI")
    return dict(ms=round(elapsed, 3), bytes=len(output.encode()), calls=count,
                correct=all(item in output for item in CASES[task]),
                digest=hashlib.sha256(output.encode()).hexdigest())


def main():
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        repo = work / "repo"
        subprocess.run(["git", "clone", "-q", "--local", "--no-checkout", ROOT, repo], check=True)
        subprocess.run(["git", "-C", repo, "checkout", "-q", "--detach", BASE], check=True)
        shims = work / "bin"
        shims.mkdir()
        (shims / "gh").write_text(FAKE_GH)
        (shims / "git").write_text('#!/bin/sh\necho git >> "$CALLS"\nexec "$REAL_GIT" "$@"\n')
        for script in shims.iterdir():
            script.chmod(0o700)
        log = work / "synthetic.log"
        log.write_text("\n".join(f"prepare fixture {i}" for i in range(48)) +
                       "\ncontract-tests | Validate OpenAPI contract | ERROR invalid synthetic contract")
        env = dict(os.environ, PATH=str(shims) + os.pathsep + os.environ["PATH"],
                   REAL_GIT=shutil.which("git"), CALLS=str(work / "calls"), SYNTHETIC_LOG=str(log))
        rows = []
        for task in CASES:
            for i in range(5):
                for mode in (("before", "after") if i % 2 == 0 else ("after", "before")):
                    rows.append(dict(task=task, round=i+1, mode=mode, **measure(repo, env, task, mode)))
        print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
