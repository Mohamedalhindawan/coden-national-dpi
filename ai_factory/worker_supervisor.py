"""Bounded one-shot supervisor for CODEN's existing synthetic-only offline worker.

This module has NO daemon loop, model adapter, API key, provider fallback,
automatic retry, task-approval authority or untrusted command execution.
The child is the fixed ai_factory.offline_worker module, not arbitrary input.
"""

import argparse
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import tempfile

from . import checkpoint

RETRY_ENABLED = False
MAX_RESULT_BYTES = 8192
MIN_GRACE_SECONDS = 10
VALID_RESULTS = frozenset({"awaiting_human_review", "blocked", "needs_review"})


class SupervisorError(ValueError):
    """Safe supervisor error without raw provider/host exception details."""


def _dir(path, *, label):
    directory = Path(path)
    if directory.is_symlink() or directory.parent.is_symlink() or not directory.is_dir():
        raise ValueError(f"trusted existing {label} directory required")
    return str(directory.resolve())


def _db(path):
    db = Path(path)
    if db.is_symlink() or db.parent.is_symlink() or not db.is_file():
        raise ValueError("trusted existing queue database required")
    return str(db.resolve())


def _result(status):
    return {"status": status, "execution_authorized": False,
            "automatic_retry_allowed": False}


def _minimal_environment():
    # Deliberately discard tokens, cloud SDK vars, proxy endpoints and
    # PYTHONPATH from the invoking shell. The operator controls PATH and
    # the trusted working tree; this is NOT a security sandbox.
    repo = str(Path(__file__).resolve().parent.parent)
    return {"PATH": os.environ.get("PATH", os.defpath),
            "PYTHONPATH": repo,
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8"}


def run_once(*, queue_db, journal, task_dir, output_root, worker_id,
             timeout_seconds=60, lease_seconds=120):
    """Operator explicitly starts ONE fixed offline synthetic worker process.

    A timeout kills its process group and never replays tasks. Existing
    queue leases expire into manual review through inspect-expired only.
    """
    checkpoint._id(worker_id)
    if type(timeout_seconds) is not int or not (1 <= timeout_seconds <= 900):
        raise ValueError("timeout must be an integer from 1 to 900 seconds")
    if type(lease_seconds) is not int or not (
        timeout_seconds + MIN_GRACE_SECONDS <= lease_seconds <= 3600
    ):
        raise ValueError("lease must exceed timeout with 10s grace; max 3600 seconds")
    db = _db(queue_db)
    journals = _dir(journal, label="journal")
    tasks = _dir(task_dir, label="task")
    outputs = _dir(output_root, label="output")
    cmd = [sys.executable, "-m", "ai_factory.offline_worker",
           "--queue-db", db, "--journal", journals, "--task-dir", tasks,
           "work-once", "--output-root", outputs,
           "--worker-id", worker_id, "--lease-seconds", str(lease_seconds)]
    try:
        with tempfile.TemporaryFile(mode="w+b") as stdout:
            proc = subprocess.Popen(cmd, cwd=str(Path(__file__).resolve().parent.parent),
                                    env=_minimal_environment(), stdin=subprocess.DEVNULL,
                                    stdout=stdout, stderr=subprocess.DEVNULL,
                                    start_new_session=True, close_fds=True)
            try:
                proc.communicate(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except OSError as exc:
                    raise SupervisorError("unable to verify child termination") from exc
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired as exc:
                    raise SupervisorError("child termination unverified") from exc
                return _result("timed_out_review_required")
            if proc.returncode != 0:
                return _result("worker_failed_review_required")
            stdout.seek(0)
            raw = stdout.read(MAX_RESULT_BYTES + 1)
            if len(raw) > MAX_RESULT_BYTES:
                return _result("untrusted_worker_result")
            try:
                parsed = json.loads(raw)
            except (UnicodeError, ValueError, TypeError):
                return _result("untrusted_worker_result")
            if parsed is None:
                return _result("idle")
            if not isinstance(parsed, dict) or parsed.get("status") not in VALID_RESULTS:
                return _result("untrusted_worker_result")
            if parsed.get("execution_authorized") is not False:
                return _result("untrusted_worker_result")
            return _result(parsed["status"])
    except OSError as exc:
        raise SupervisorError("operator supervisor unable to launch or supervise child") from exc


def make_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue-db", type=Path, required=True)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--task-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--worker-id", default="offline_operator")
    parser.add_argument("--timeout-seconds", type=int, default=60)
    parser.add_argument("--lease-seconds", type=int, default=120)
    actions = parser.add_subparsers(dest="command", required=True)
    actions.add_parser("work-once", help="supervise one operator-authorized synthetic run")
    return parser


def main(argv=None):
    args = make_parser().parse_args(argv)
    try:
        outcome = run_once(queue_db=args.queue_db, journal=args.journal,
                           task_dir=args.task_dir, output_root=args.output_root,
                           worker_id=args.worker_id, timeout_seconds=args.timeout_seconds,
                           lease_seconds=args.lease_seconds)
    except (OSError, ValueError):
        print("Supervisor blocked; inspect local queue and checkpoint evidence", file=sys.stderr)
        return 2
    print(json.dumps(outcome, sort_keys=True))
    return 0 if outcome["status"] in ("idle", "awaiting_human_review") else 1


if __name__ == "__main__":
    raise SystemExit(main())
