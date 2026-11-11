"""Read-only, fail-closed JSON task batch review for CODEN AI Factory.

This is not an executor. It never approves tasks or performs requested actions.
"""
import argparse
import json
from pathlib import Path
from .intake import make_execution_plan, validate_intake


def prepare_review_queue(tasks):
    if not isinstance(tasks, list) or not tasks:
        return {'valid': False, 'plans': [], 'errors': [{'index': None, 'reason': 'tasks must be a nonempty array'}]}
    errors = []
    seen = set()
    for index, task in enumerate(tasks):
        result = validate_intake(task)
        for reason in result['errors']:
            errors.append({'index': index, 'reason': reason})
        if isinstance(task, dict) and isinstance(task.get('id'), str) and task['id'].strip():
            if task['id'] in seen:
                errors.append({'index': index, 'reason': 'duplicate task id'})
            seen.add(task['id'])
    if errors:
        return {'valid': False, 'plans': [], 'errors': errors}
    return {'valid': True, 'plans': [make_execution_plan(task) for task in tasks], 'errors': []}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Offline synthetic-only CODEN review queue (never executes tasks)')
    parser.add_argument('input', help='Path to JSON array of synthetic tasks')
    args = parser.parse_args(argv)
    try:
        tasks = json.loads(Path(args.input).read_text(encoding='utf-8'))
        result = prepare_review_queue(tasks)
    except (OSError, UnicodeError, ValueError) as exc:
        result = {'valid': False, 'plans': [], 'errors': [{'index': None, 'reason': type(exc).__name__}]}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result['valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
