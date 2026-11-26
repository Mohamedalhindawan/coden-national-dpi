"""Opt-in **offline synthetic-only** queue-to-checkpoint project worker.

This is an operator-invoked, single-task execution adapter, NOT a daemon,
provider router, general coding agent, production approval or autonomous retry.
The existing project.run controls all untrusted candidate code sandboxing.
Never use this on real citizen/government/customer data.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import sys

from . import checkpoint, durable_queue, project

MAX_TASK_BYTES = 32768


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _task_file(tasks_dir, task_id):
    checkpoint._id(task_id)
    folder = Path(tasks_dir)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("operator task directory required")
    return folder / (task_id + ".json")


def _read_task_bytes(path):
    path = path.absolute()
    if ".." in path.parts:
        raise ValueError("unexpected parent traversal in task path")
    # O_NOFOLLOW on only the leaf cannot prevent an intermediate symlink.
    # Pin every directory with a descriptor, as in the multifile reviewer,
    # and read relative to the last pinned directory rather than re-resolving
    # a mutable pathname between validation and use.
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    parent_fd = os.open(path.anchor, flags)
    try:
        for part in path.parts[1:-1]:
            next_fd = os.open(part, flags, dir_fd=parent_fd)
            os.close(parent_fd)
            parent_fd = next_fd
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                     dir_fd=parent_fd)
    finally:
        os.close(parent_fd)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_TASK_BYTES:
            raise ValueError("task must be a bounded regular file")
        with os.fdopen(os.dup(fd), "rb") as stream:
            data = stream.read(MAX_TASK_BYTES + 1)
        if len(data) > MAX_TASK_BYTES:
            raise ValueError("task exceeds size limit")
    finally:
        os.close(fd)
    return data


def _read_task(tasks_dir, task_id):
    data = _read_task_bytes(_task_file(tasks_dir, task_id))
    digest = hashlib.sha256(data).hexdigest()
    task = json.loads(data.decode("utf-8"), object_pairs_hook=_unique_keys)
    return task, digest


def _load_task(tasks_dir, task_id):
    task, digest = _read_task(tasks_dir, task_id)
    if not project.valid(task) or task["id"] != task_id or task["recipe"] != "status-counts":
        raise ValueError("only approved synthetic status-counts pilot tasks supported")
    return task, digest


def prepare_modeb_trial(tasks_dir, task_id, *, branch, commit):
    """Bind existing worker task bytes to the reviewed Mode B request.

    This deliberately has no queue or lease side effect. The existing
    synthetic worker cannot claim this recipe; an independently admitted
    one-shot execution supervisor must later own that transition.
    """
    from . import openhands_sdk_operator

    checkpoint._branch(branch)
    checkpoint._commit(commit)
    if not branch or not commit or task_id != "OPENHANDS_SYNTHETIC_1":
        raise ValueError("explicit first Mode B task and source identity required")
    task, digest = _read_task(tasks_dir, task_id)
    request = openhands_sdk_operator.prepare_modeb_request(task)
    return {
        "status": "modeb_intent_prepared_review_required",
        "branch": branch,
        "commit": commit,
        "task_file_sha256": digest,
        "request": request,
        "queue_enqueued": False,
        "lease_claimed": False,
        "execution_authorized": False,
        "release_authorized": False,
        "automatic_retry_allowed": False,
    }


def run_modeb_fixture_trial(tasks_dir, task_id, *, branch, commit,
                            expected_task_file_sha256, allow_agent=False,
                            fixture_only=False, fixture_adapter=None, cancelled=None):
    """Run the existing bridge against trusted fixtures only, without a lease.

    The caller supplies the expected raw file hash and reviewed source
    identity; this function does not inspect a Git checkout or authorize
    real execution. Read the task once, then bind the request and receipt.
    """
    from . import openhands_sdk_operator

    checkpoint._branch(branch)
    checkpoint._commit(commit)
    if not branch or not commit or task_id != "OPENHANDS_SYNTHETIC_1":
        raise ValueError("explicit first Mode B task and source identity required")
    task, digest = _read_task(tasks_dir, task_id)
    if type(expected_task_file_sha256) is not str or digest != expected_task_file_sha256:
        raise ValueError("task file identity mismatch")
    source = {"branch": branch, "commit": commit, "task_file_sha256": digest}
    result = openhands_sdk_operator.run_modeb_once(
        task=task, source_identity=source, allow_agent=allow_agent,
        fixture_only=fixture_only, fixture_adapter=fixture_adapter, cancelled=cancelled)
    return dict(result, source_identity=source, queue_enqueued=False,
                lease_claimed=False, source_checkout_verified=False)


def _verified_modeb_task(checkout_root, lease):
    """Read one tracked task from a trusted, operator-owned SHA-1 checkout.

    The operator admits the commit and owns the Git metadata and queue. Verify
    the selected branch, commit and task bytes only, not unrelated worktree
    files. The parsed bytes below are the only checkout data sent to the bridge.
    """
    root = Path(checkout_root).absolute()
    task_path = "ai_factory/examples/openhands-multifile-task.json"

    def git(*args):
        # Do not inherit Git overrides, credentials or partial-clone transports.
        return subprocess.run(
            ["git", "--no-replace-objects", *args], cwd=root,
            env={"PATH": os.defpath, "GIT_CONFIG_NOSYSTEM": "1",
                 "GIT_CONFIG_GLOBAL": os.devnull, "GIT_ALLOW_PROTOCOL": "",
                 "GIT_TERMINAL_PROMPT": "0", "GIT_CEILING_DIRECTORIES": str(root.parent)},
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            check=True, timeout=5).stdout

    branch_ref = ("refs/heads/" + lease["branch"] + "\n").encode()
    commit = lease["commit"]
    if (git("rev-parse", "--is-inside-work-tree", "--show-prefix") != b"true\n\n"
            or git("symbolic-ref", "HEAD") != branch_ref
            or git("rev-parse", "--verify", "HEAD^{commit}") != (commit + "\n").encode()):
        raise ValueError("checkout identity mismatch")
    raw = _read_task_bytes(root / task_path)
    if hashlib.sha256(raw).hexdigest() != lease["task_sha256"]:
        raise ValueError("queued task identity mismatch")
    # Git's SHA-1 object id includes the object type, decimal size and NUL.
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw,
                        usedforsecurity=False).hexdigest()
    expected_entry = f"100644 blob {blob}\t{task_path}\0".encode()
    if git("ls-tree", "-z", commit, "--", task_path) != expected_entry:
        raise ValueError("task differs from committed regular file")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_keys)


def work_modeb_fixture_once(queue, checkout_root, *, worker_id, fixture_adapter,
                            lease_seconds=60):
    """Process only the pinned Mode B fixture in an operator-owned fixture queue.

    The trusted adapter is injected, with no SDK or model path. Cancellation
    and lease validity are checked at dispatch and receipt boundaries, not
    asynchronously inside adapter code. An uncertain attempt is never retried.
    """
    from . import openhands_sdk_operator

    if fixture_adapter is None:
        raise ValueError("trusted fixture adapter required")
    task_id = "OPENHANDS_SYNTHETIC_1"
    lease = queue.claim(worker_id, task_id=task_id, lease_seconds=lease_seconds)
    if lease is None:
        return None
    token = lease["lease_token"]
    source = {"branch": lease["branch"], "commit": lease["commit"],
              "task_file_sha256": lease["task_sha256"]}
    verified = False

    def receipt(status):
        return dict(_public(lease, status), source_identity=source, lease_claimed=True,
                    source_checkout_verified=verified, automatic_retry_allowed=False,
                    release_authorized=False)

    def check_lease():
        queue.heartbeat(task_id, token, extend_seconds=lease_seconds)
        return False  # The bridge treats a raised verification error as a stop.

    try:
        task = _verified_modeb_task(checkout_root, lease)
        verified = True
    except (OSError, ValueError, subprocess.SubprocessError):
        result = None
    else:
        try:
            result = openhands_sdk_operator.run_modeb_once(
                task=task, source_identity=source, allow_agent=True, fixture_only=True,
                fixture_adapter=fixture_adapter, cancelled=check_lease)
        except Exception:
            # Dispatch may already have occurred. Leave the lease for quarantine.
            return receipt("needs_review")

    if result and result["fixture_adapter_attempted"]:
        if result["status"] != "fixture_completed_review_required":
            return dict(receipt("needs_review"), bridge_status=result["status"])
        outcome = "awaiting_human_review"
    else:
        outcome = "blocked"
    try:
        queue.finish(task_id, token, outcome)
    except (ValueError, OSError, sqlite3.Error):
        # Expired/cancelled lease or uncertain store write: preserve for review.
        return receipt("needs_review")
    if result and outcome == "awaiting_human_review":
        return dict(result, **receipt(result["status"]))
    return dict(receipt("blocked"), bridge_status=result["status"] if result else None)


def submit(queue, checkpoint_root, tasks_dir, task_id, *, branch, commit):
    """Register a pre-existing trusted synthetic JSON task (never runs it)."""
    task, digest = _load_task(tasks_dir, task_id)
    checkpoint._branch(branch)
    checkpoint._commit(commit)
    if not branch or not commit:
        raise ValueError("branch and full commit required")
    # Checkpoint comes first. If queue insertion fails, leave an orphan record
    # for operator inspection; never silently recover or re-enqueue.
    checkpoint.create(checkpoint_root, task_id, branch=branch, commit=commit)
    return queue.enqueue(task_id, branch, commit, digest)


def submit_idempotent(queue, checkpoint_root, tasks_dir, task_id, *, branch, commit):
    """Register once or return an existing matching receipt, never replay work.

    The operator owns both stores. This is not an atomic cross-store transaction:
    a concurrent first submission may be rejected and an orphan requires review.
    The strict submit API remains unchanged.
    """
    _, digest = _load_task(tasks_dir, task_id)
    checkpoint._branch(branch)
    checkpoint._commit(commit)
    if not branch or not commit:
        raise ValueError("branch and full commit required")
    try:
        state = queue.read(task_id)
    except ValueError as exc:
        if str(exc) != "unknown task":
            raise
        # Exclusive journal creation prevents duplicate admissions and refuses
        # an orphan. Do not retry or delete a journal after a failed enqueue.
        checkpoint.create(checkpoint_root, task_id, branch=branch, commit=commit)
        return queue.enqueue(task_id, branch, commit, digest)
    if (state["branch"], state["commit"], state["task_sha256"]) != (branch, commit, digest):
        raise ValueError("admission identity conflict")
    journal = checkpoint.read(checkpoint_root, task_id)
    if (journal["last_branch"], journal["last_commit"]) != (branch, commit):
        raise ValueError("admission journal identity conflict")
    if state["status"] == "queued" and journal["status"] != "prepared":
        raise ValueError("queued admission requires a prepared journal")
    # Receipt only: no status update, lease extension, retry or approval.
    return state


def _public(lease, status, *, directory=None):
    result = {
        "task_id": lease["task_id"],
        "status": status,
        "execution_authorized": False,
    }
    if directory is not None:
        result["directory"] = Path(directory)
    return result


def work_once(queue, checkpoint_root, tasks_dir, output_root, *, worker_id, lease_seconds=300, task_id=None):
    """Claim one task and run existing bounded pilot; no unattended retries."""
    if not Path(output_root).is_dir() or Path(output_root).is_symlink():
        raise ValueError("existing operator output directory required")
    # Explicit task binding prevents a supervisor watching task A from
    # accidentally launching another queued task B. The legacy default
    # remains FIFO for operator-invoked unmonitored pilots.
    if task_id is None:
        lease = queue.claim(worker_id, lease_seconds=lease_seconds)
    else:
        checkpoint._id(task_id)
        lease = queue.claim(worker_id, lease_seconds=lease_seconds, task_id=task_id)
    if lease is None:
        return None
    task_id = lease["task_id"]
    token = lease["lease_token"]
    execution_started = False
    try:
        task, digest = _load_task(tasks_dir, task_id)
        original = checkpoint.read(checkpoint_root, task_id)
        if (digest != lease["task_sha256"] or
            original["last_branch"] != lease["branch"] or
            original["last_commit"] != lease["commit"] or
            original["status"] != "prepared"):
            raise ValueError("task or checkpoint integrity mismatch")
        # Verifies this claim remains current before any work starts.
        queue.heartbeat(task_id, token, extend_seconds=lease_seconds)
        checkpoint.record(checkpoint_root, task_id, event="checkpoint",
                          next_action="offline_project_run", event_key="worker_start")
        execution_started = True
        directory, outcome = project.run(task, output_root)
        if outcome == "awaiting_human_review":
            checkpoint.record(checkpoint_root, task_id, event="review_requested",
                              next_action="human_review", event_key="worker_review")
            queue.finish(task_id, token, "awaiting_human_review")
            return _public(lease, "awaiting_human_review", directory=directory)
        if outcome not in ("blocked", "failed"):
            raise ValueError("unrecognized project outcome")
        checkpoint.record(checkpoint_root, task_id, event="blocked",
                          next_action="inspect_offline_logs", event_key="worker_block")
        queue.finish(task_id, token, "blocked")
        return _public(lease, "blocked", directory=directory)
    except Exception:
        # Once the project runner has been invoked, it may have created files
        # even if an exception is raised or a subsequent journal/DB write fails.
        # Leave the lease intact for expiry quarantine + operator reconciliation:
        # do not overwrite review evidence with a false terminal "blocked".
        if execution_started:
            return _public(lease, "needs_review")
        # An explicit SIGKILL or KeyboardInterrupt escapes: after lease expiry,
        # recover_expired quarantines instead of automatically re-running.
        # Do not log raw exception details (they may contain task/secret data).
        journal_ok = True
        try:
            checkpoint.record(checkpoint_root, task_id, event="blocked",
                              next_action="inspect_offline_logs", event_key="worker_block")
        except (OSError, ValueError, TypeError):
            journal_ok = False
        try:
            queue.finish(task_id, token, "blocked")
        except (OSError, ValueError):
            return _public(lease, "needs_review")
        return _public(lease, "blocked" if journal_ok else "needs_review")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue-db", type=Path, required=True)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--task-dir", type=Path, required=True)
    modes = parser.add_subparsers(dest="command", required=True)
    submit_cmd = modes.add_parser("submit", help="Operator registers synthetic task without running it")
    submit_cmd.add_argument("task_id")
    submit_cmd.add_argument("--branch", required=True)
    submit_cmd.add_argument("--commit", required=True)
    once = modes.add_parser("work-once", help="Operator explicitly processes at most one queued task")
    once.add_argument("--output-root", type=Path, required=True)
    once.add_argument("--worker-id", default="offline_operator")
    once.add_argument("--lease-seconds", type=int, default=300)
    once.add_argument("--task-id", help="Bind one operator-owned worker to a specific task")
    cancel = modes.add_parser("request-cancel", help="Operator-only request; never kill/retry running code")
    cancel.add_argument("task_id")
    modes.add_parser("inspect-expired", help="Quarantine expired leases, never replay")
    args = parser.parse_args(argv)
    try:
        q = durable_queue.DurableQueue(args.queue_db)
        if args.command == "submit":
            output = submit(q, args.journal, args.task_dir, args.task_id, branch=args.branch, commit=args.commit)
        elif args.command == "work-once":
            output = work_once(q, args.journal, args.task_dir, args.output_root,
                               worker_id=args.worker_id, lease_seconds=args.lease_seconds,
                               task_id=args.task_id)
        elif args.command == "request-cancel":
            output = q.request_cancel(args.task_id)
        else:
            output = {"quarantined": q.recover_expired(), "execution_authorized": False}
    except (OSError, ValueError, TypeError) as exc:
        print(f"Operator worker blocked ({type(exc).__name__})", file=sys.stderr)
        return 2
    if output is not None and "directory" in output:
        output["directory"] = str(output["directory"])
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
