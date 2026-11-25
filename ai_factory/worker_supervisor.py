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
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time

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


def _unique_json_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate worker result field")
        result[key] = value
    return result


def _result(status):
    return {"status": status, "execution_authorized": False,
            "automatic_retry_allowed": False}


def _terminate_process_group(proc):
    """Best-effort cancellation with verified leader exit; no automatic replay.

    Only use for a child launched with start_new_session=True. The caller
    must keep all task state for operator review after an uncertain outcome.
    """
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass  # Group already exited; still reap/verify the process leader.
    except OSError as exc:
        raise SupervisorError("unable to verify child termination") from exc
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired as exc:
        raise SupervisorError("child termination unverified") from exc


def _minimal_environment():
    # Deliberately discard tokens, cloud SDK vars, proxy endpoints and
    # PYTHONPATH from the invoking shell. The operator controls PATH and
    # the trusted working tree; this is NOT a security sandbox.
    repo = str(Path(__file__).resolve().parent.parent)
    return {"PATH": os.environ.get("PATH", os.defpath),
            "PYTHONPATH": repo,
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8"}


def _monitor_bound_task(proc, *, queue_db, journal, task_id, timeout_seconds):
    """Watch only the selected worker task; stop only our owned child group.

    A process-group SIGKILL followed by wait() confirms the leader was reaped,
    NOT that all its descendants vanished or that the task can be retried.
    Queue status and journal remain review-only and fail closed.
    """
    from .durable_queue import DurableQueue

    def monitor_read(read):
        try:
            return read()
        except (OSError, sqlite3.Error, ValueError, TypeError, KeyError) as exc:
            # Lost durable state is not permission to keep executing.
            # Stop only the owned process group; preserve the lease for review.
            if proc.returncode is None:
                _terminate_process_group(proc)
            raise SupervisorError("worker queue monitoring failed; operator review required") from exc

    queue = monitor_read(lambda: DurableQueue(queue_db))
    deadline = time.monotonic() + timeout_seconds
    while True:
        state = monitor_read(lambda: queue.read(task_id)["status"])
        if state in ("cancel_requested", "cancelled", "needs_review"):
            if proc.returncode is None:
                _terminate_process_group(proc)
            else:
                proc.wait(timeout=0)
            # This is an evidence record, not a declaration of safe finality.
            # If it fails, refuse any success receipt; queue remains pending.
            try:
                checkpoint.record(
                    journal, task_id, event="blocked",
                    next_action="inspect_cancel_stop",
                    event_key="supervisor_cancel_stop",
                )
            except (OSError, ValueError, TypeError) as exc:
                raise SupervisorError("cancelled child journal unverified; operator review required") from exc
            return dict(
                _result("cancel_stop_review_required"),
                owned_process_leader_reaped=True,
                process_tree_absence_verified=False,
                queue_state=state,
                queue_reconciliation_required=True,
            )
        if state not in (
            "queued", "leased", "awaiting_human_review", "blocked",
            "failed", "needs_review",
        ):
            # Unexpected queue transition cannot permit child continuation.
            if proc.returncode is None:
                _terminate_process_group(proc)
            raise SupervisorError("unexpected task state; operator reconciliation required")
        remaining = deadline - __import__("time").monotonic()
        if remaining <= 0:
            if proc.returncode is None:
                _terminate_process_group(proc)
            return _result("timed_out_review_required")
        try:
            proc.wait(timeout=min(0.10, remaining))
        except subprocess.TimeoutExpired:
            continue
        except OSError as exc:
            if proc.returncode is None:
                _terminate_process_group(proc)
            raise SupervisorError("worker wait failed; operator review required") from exc
        # Exit can race with a cancel request. Re-read at least once so a
        # successful child exit never masks an already registered cancel.
        final_state = monitor_read(lambda: queue.read(task_id)["status"])
        if final_state in ("cancel_requested", "cancelled", "needs_review"):
            continue
        if final_state == "queued":
            return _result("target_not_claimed_review_required")
        return None


def run_once(*, queue_db, journal, task_dir, output_root, worker_id,
             timeout_seconds=60, lease_seconds=120, task_id=None):
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
    if task_id is not None:
        checkpoint._id(task_id)
        from .durable_queue import DurableQueue
        if DurableQueue(db).read(task_id)["status"] != "queued":
            raise ValueError("explicit task is not currently queued; do not spawn")
    journals = _dir(journal, label="journal")
    tasks = _dir(task_dir, label="task")
    outputs = _dir(output_root, label="output")
    cmd = [sys.executable, "-m", "ai_factory.offline_worker",
           "--queue-db", db, "--journal", journals, "--task-dir", tasks,
           "work-once", "--output-root", outputs,
           "--worker-id", worker_id, "--lease-seconds", str(lease_seconds)]
    if task_id is not None:
        cmd.extend(["--task-id", task_id])
    try:
        with tempfile.TemporaryFile(mode="w+b") as stdout:
            proc = subprocess.Popen(cmd, cwd=str(Path(__file__).resolve().parent.parent),
                                    env=_minimal_environment(), stdin=subprocess.DEVNULL,
                                    stdout=stdout, stderr=subprocess.DEVNULL,
                                    start_new_session=True, close_fds=True)
            if task_id is not None:
                # NEW opt-in branch: actual SQLite cancellation is monitored
                # while our single explicitly bound child is running.
                monitored = _monitor_bound_task(
                    proc, queue_db=db, journal=journals,
                    task_id=task_id, timeout_seconds=timeout_seconds
                )
                if monitored is not None:
                    return monitored
            else:
                # Preserve the proven old operator-only FIFO path.
                try:
                    proc.communicate(timeout=timeout_seconds)
                except subprocess.TimeoutExpired:
                    _terminate_process_group(proc)
                    return _result("timed_out_review_required")
                except OSError as exc:
                    _terminate_process_group(proc)
                    raise SupervisorError("worker communication failed; manual review required") from exc
            if proc.returncode != 0:
                return _result("worker_failed_review_required")
            stdout.seek(0)
            raw = stdout.read(MAX_RESULT_BYTES + 1)
            if len(raw) > MAX_RESULT_BYTES:
                return _result("untrusted_worker_result")
            try:
                parsed = json.loads(raw, object_pairs_hook=_unique_json_keys)
            except (UnicodeError, ValueError, TypeError):
                return _result("untrusted_worker_result")
            if parsed is None:
                # A bound child must account for its selected task. A null
                # receipt cannot establish that a claimed task was idle.
                return _result("untrusted_worker_result" if task_id is not None else "idle")
            required = {"task_id", "status", "execution_authorized"}
            if not isinstance(parsed, dict) or set(parsed) not in (
                required, required | {"directory"}
            ):
                return _result("untrusted_worker_result")
            try:
                checkpoint._id(parsed["task_id"])
            except (ValueError, TypeError):
                return _result("untrusted_worker_result")
            if task_id is not None and parsed["task_id"] != task_id:
                return _result("untrusted_worker_result")
            status = parsed["status"]
            if not isinstance(status, str) or status not in VALID_RESULTS:
                return _result("untrusted_worker_result")
            if parsed["execution_authorized"] is not False:
                return _result("untrusted_worker_result")
            if task_id is not None:
                from .durable_queue import DurableQueue
                try:
                    state = DurableQueue(db).read(task_id)["status"]
                except (OSError, sqlite3.Error, ValueError, TypeError, KeyError) as exc:
                    # The child has already exited; do not approve its receipt
                    # when the final durable state cannot be independently read.
                    raise SupervisorError("final worker state unverified; operator review required") from exc
                expected = {
                    "awaiting_human_review": "awaiting_human_review",
                    "blocked": "blocked",
                    "needs_review": "needs_review",
                }
                if state != expected.get(status):
                    return _result("untrusted_worker_result")
            if "directory" in parsed:
                dirname = parsed["directory"]
                if not isinstance(dirname, str) or not dirname or len(dirname) > 4096:
                    return _result("untrusted_worker_result")
                # The child cannot claim an output outside the operator's root.
                candidate = Path(dirname)
                if not candidate.is_absolute() or not candidate.resolve().is_relative_to(outputs):
                    return _result("untrusted_worker_result")
            return _result(status)
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
    parser.add_argument("--task-id", help="Bind monitored one-shot child to this queue task only")
    actions = parser.add_subparsers(dest="command", required=True)
    actions.add_parser("work-once", help="supervise one operator-authorized synthetic run")
    return parser


def main(argv=None):
    args = make_parser().parse_args(argv)
    try:
        outcome = run_once(queue_db=args.queue_db, journal=args.journal,
                           task_dir=args.task_dir, output_root=args.output_root,
                           worker_id=args.worker_id, timeout_seconds=args.timeout_seconds,
                           lease_seconds=args.lease_seconds, task_id=args.task_id)
    except (OSError, ValueError):
        print("Supervisor blocked; inspect local queue and checkpoint evidence", file=sys.stderr)
        return 2
    print(json.dumps(outcome, sort_keys=True))
    return 0 if outcome["status"] in ("idle", "awaiting_human_review") else 1


if __name__ == "__main__":
    raise SystemExit(main())
