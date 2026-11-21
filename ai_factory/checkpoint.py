"""Offline, append-only CODEN factory checkpoint journal (no task execution).

This module *records* progress. It cannot approve, run or resume agents, invoke
models, change GitHub, spend money or perform provider fallbacks. Its hash chain
helps detect accidental file changes; it is not a signature against an attacker
with write access. Store journals outside agent-writeable workspaces.
"""

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from uuid import uuid4

ID = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
BRANCH = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}\Z")
ACTION = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,79}\Z")
SHA = re.compile(r"[a-f0-9]{40}\Z")
MAX_BYTES = 1024 * 1024
MAX_EVENTS = 1000
PAUSES = frozenset({"quota_exceeded", "rate_limited", "context_exceeded", "provider_unavailable", "budget_exceeded", "worker_failed"})
EVENTS = frozenset({"checkpoint", "review_requested", "resume_requested", "blocked"}) | PAUSES
ZERO = "0" * 64


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode("utf-8")


def _id(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError("invalid task id")
    return value


def _branch(value):
    if value is not None and (
        not isinstance(value, str)
        or not BRANCH.fullmatch(value)
        or ".." in value
        or "//" in value
        or value.endswith(("/", "."))
    ):
        raise ValueError("invalid branch")
    return value


def _commit(value):
    if value is not None and (not isinstance(value, str) or not SHA.fullmatch(value)):
        raise ValueError("invalid commit")
    return value


def _action(value):
    if value is not None and (not isinstance(value, str) or not ACTION.fullmatch(value)):
        raise ValueError("invalid next action id")
    return value


def _key(value):
    if not isinstance(value, str) or not ACTION.fullmatch(value):
        raise ValueError("invalid idempotency key")
    return value


def _path(root, task_id):
    _id(task_id)
    folder = Path(root)
    if folder.is_symlink():
        raise ValueError("symlink checkpoint root is forbidden")
    return folder / f"{task_id}.jsonl"


def _read_locked(fd):
    size = os.fstat(fd).st_size
    if size > MAX_BYTES or not stat.S_ISREG(os.fstat(fd).st_mode):
        raise ValueError("invalid journal file")
    os.lseek(fd, 0, os.SEEK_SET)
    with os.fdopen(os.dup(fd), "rb") as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES or not raw or not raw.endswith(b"\n"):
        raise ValueError("missing or incomplete journal")
    try:
        records = [json.loads(line) for line in raw.splitlines()]
    except (ValueError, UnicodeError) as exc:
        raise ValueError("malformed journal") from exc
    if not 1 <= len(records) <= MAX_EVENTS:
        raise ValueError("invalid journal length")
    prev = ZERO
    for number, record in enumerate(records, start=1):
        if not isinstance(record, dict) or set(record) != {
            "seq", "event", "at", "branch", "commit", "next_action", "key", "prev_sha256", "sha256"
        }:
            raise ValueError("invalid journal record")
        saved = record["sha256"]
        payload = {k: v for k, v in record.items() if k != "sha256"}
        if (
            type(record["seq"]) is not int
            or record["seq"] != number
            or record["prev_sha256"] != prev
            or saved != hashlib.sha256(_canonical(payload)).hexdigest()
        ):
            raise ValueError("journal hash chain invalid")
        _branch(record["branch"])
        _commit(record["commit"])
        _action(record["next_action"])
        _key(record["key"])
        if not isinstance(record["at"], str):
            raise ValueError("invalid record time")
        prev = saved
    _state(records)  # Validate event order before allowing new writes.
    return records


def _state(records):
    first = records[0]
    if first["event"] != "created" or first["branch"] is None or first["commit"] is None:
        raise ValueError("journal missing initial record")
    status = "prepared"
    reason = None
    last_branch = first["branch"]
    last_commit = first["commit"]
    next_action = first["next_action"]
    keys = set()
    for index, entry in enumerate(records):
        event = entry["event"]
        if entry["key"] in keys or (index > 0 and event not in EVENTS):
            raise ValueError("duplicate or unsupported journal event")
        keys.add(entry["key"])
        if index:
            if event == "resume_requested":
                if status not in ("paused", "blocked"):
                    raise ValueError("resume requires paused or blocked state")
                status = "pending_human_resume"
                reason = None
            elif event == "checkpoint":
                if status not in ("prepared", "checkpointed", "pending_human_resume"):
                    raise ValueError("cannot checkpoint paused or finalized task")
                status = "checkpointed"
                reason = None
            elif event in PAUSES:
                if status == "awaiting_human_review":
                    raise ValueError("review state cannot be paused")
                status = "paused"
                reason = event
            elif event == "blocked":
                status = "blocked"
                reason = event
            elif event == "review_requested":
                if status not in ("prepared", "checkpointed", "pending_human_resume"):
                    raise ValueError("cannot request review from paused state")
                status = "awaiting_human_review"
                reason = None
        if entry["branch"] is not None:
            last_branch = entry["branch"]
        if entry["commit"] is not None:
            last_commit = entry["commit"]
        if entry["next_action"] is not None:
            next_action = entry["next_action"]
    return {
        "status": status,
        "pause_reason": reason,
        "last_branch": last_branch,
        "last_commit": last_commit,
        "next_action": next_action,
        "last_event": records[-1]["event"],
        "event_count": len(records),
        "execution_authorized": False,
        "verified": True,
    }


def _entry(number, event, branch, commit, next_action, key, previous):
    payload = {
        "seq": number,
        "event": event,
        "at": datetime.now(timezone.utc).isoformat(),
        "branch": branch,
        "commit": commit,
        "next_action": next_action,
        "key": key,
        "prev_sha256": previous,
    }
    return dict(payload, sha256=hashlib.sha256(_canonical(payload)).hexdigest())


def _write_all(fd, data):
    view = memoryview(data)
    while view:
        count = os.write(fd, view)
        if count < 1:
            raise OSError("short journal write")
        view = view[count:]
    os.fsync(fd)


def create(root, task_id, *, branch, commit):
    path = _path(root, task_id)
    _branch(branch)
    _commit(commit)
    if branch is None or commit is None:
        raise ValueError("branch and full commit SHA required")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    record = _entry(1, "created", branch, commit, None, "init", ZERO)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        _write_all(fd, _canonical(record) + b"\n")
    finally:
        os.close(fd)
    return dict(task_id=task_id, **_state([record]))


def read(root, task_id):
    path = _path(root, task_id)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        fcntl.flock(fd, fcntl.LOCK_SH)
        records = _read_locked(fd)
        return dict(task_id=task_id, **_state(records))
    finally:
        os.close(fd)


def record(root, task_id, *, event, branch=None, commit=None, next_action=None, event_key=None):
    path = _path(root, task_id)
    if event not in EVENTS:
        raise ValueError("unsupported event")
    _branch(branch)
    _commit(commit)
    _action(next_action)
    key = _key(event_key) if event_key is not None else uuid4().hex
    fd = os.open(path, os.O_RDWR | os.O_NOFOLLOW)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        events = _read_locked(fd)
        for old in events:
            if old["key"] == key:
                if (old["event"], old["branch"], old["commit"], old["next_action"]) == (event, branch, commit, next_action):
                    return dict(task_id=task_id, **_state(events))
                raise ValueError("idempotency key conflict")
        if len(events) >= MAX_EVENTS:
            raise ValueError("journal is full")
        new = _entry(len(events) + 1, event, branch, commit, next_action, key, events[-1]["sha256"])
        _state(events + [new])  # Fail before writing on invalid transition.
        data = _canonical(new) + b"\n"
        if os.fstat(fd).st_size + len(data) > MAX_BYTES:
            raise ValueError("journal size limit exceeded")
        os.lseek(fd, 0, os.SEEK_END)
        _write_all(fd, data)
        return dict(task_id=task_id, **_state(events + [new]))
    finally:
        os.close(fd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True, help="Operator-owned journal directory")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("create", help="Create a non-executing task record")
    init.add_argument("task_id")
    init.add_argument("--branch", required=True)
    init.add_argument("--commit", required=True)
    add = sub.add_parser("record", help="Record a pause, checkpoint or review request")
    add.add_argument("task_id")
    add.add_argument("--event", choices=sorted(EVENTS), required=True)
    add.add_argument("--branch")
    add.add_argument("--commit")
    add.add_argument("--next-action")
    add.add_argument("--event-key")
    show = sub.add_parser("show", help="Read and verify a stored task record")
    show.add_argument("task_id")
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            result = create(args.store, args.task_id, branch=args.branch, commit=args.commit)
        elif args.command == "record":
            result = record(args.store, args.task_id, event=args.event, branch=args.branch,
                            commit=args.commit, next_action=args.next_action, event_key=args.event_key)
        else:
            result = read(args.store, args.task_id)
    except (OSError, ValueError, TypeError) as exc:
        print(f"Checkpoint error ({type(exc).__name__})", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
