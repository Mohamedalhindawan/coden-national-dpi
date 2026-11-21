"""Offline CODEN quota/failure recovery plan CLI: NEVER dispatches a model.

Usage: python -m ai_factory.recovery_cli --input configs/model_recovery.example.json
Optional operator journal recording requires an existing checkpoint task.
"""

import argparse
import json
import os
from pathlib import Path
import stat
import sys

from . import recovery_policy, recovery_checkpoint

MAX_INPUT_BYTES = 32768
INPUT_KEYS = frozenset({'observation', 'task', 'routes', 'failed_provider'})


def _no_duplicates(pairs):
    record = {}
    for key, value in pairs:
        if key in record:
            raise ValueError('duplicate JSON key')
        record[key] = value
    return record


def _load(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode) or os.fstat(fd).st_size > MAX_INPUT_BYTES:
            raise ValueError('invalid input file')
        with os.fdopen(os.dup(fd), 'rb') as stream:
            raw = stream.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError('input size exceeded')
        data = json.loads(raw, object_pairs_hook=_no_duplicates)
        if not isinstance(data, dict) or set(data) != INPUT_KEYS:
            raise ValueError('invalid input schema')
        return data
    finally:
        os.close(fd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Small, credential-free JSON input')
    parser.add_argument('--store', type=Path, help='Existing operator-owned checkpoint store')
    parser.add_argument('--task-id', help='Existing checkpoint task ID; required with --store')
    parser.add_argument('--event-key', help='Optional idempotency key')
    args = parser.parse_args(argv)
    if bool(args.store) != bool(args.task_id) or (args.event_key and not args.store):
        parser.error('--store and --task-id must be passed together; --event-key requires both')
    try:
        data = _load(args.input)
        options = {'failed_provider': data['failed_provider']}
        if args.store:
            result = recovery_checkpoint.record_recovery(args.store, args.task_id,
                data['observation'], data['task'], data['routes'], event_key=args.event_key, **options)
        else:
            plan = recovery_policy.plan_recovery(data['observation'], data['task'],
                data['routes'], **options)
            result = {'plan': plan}
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        # Never output upstream input content, credentials, or raw provider exception messages.
        print(f'Recovery planning blocked ({type(exc).__name__})', file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
