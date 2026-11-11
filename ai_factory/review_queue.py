"""Read-only, fail-closed JSON task batch review for CODEN AI Factory.

This is not an executor. It never approves tasks or performs requested actions.
"""
import argparse
import json
from pathlib import Path
from decimal import Decimal, InvalidOperation
from .intake import make_execution_plan, validate_intake


def prepare_review_queue(tasks, budget_usd=None):
    if not isinstance(tasks, list) or not tasks:
        return {'valid': False, 'plans': [], 'errors': [{'index': None, 'reason': 'tasks must be a nonempty array'}]}
    errors = []
    seen = set()
    total = Decimal('0')
    if budget_usd is not None:
        try:
            limit = Decimal(str(budget_usd))
            if not limit.is_finite() or limit < 0:
                raise ValueError('invalid budget')
        except (InvalidOperation, ValueError):
            return {'valid': False, 'plans': [], 'errors': [{'index': None, 'reason': 'invalid budget'}]}

    for index, task in enumerate(tasks):
        result = validate_intake(task)
        if budget_usd is not None:
            try:
                value = task.get('estimated_cost_usd') if isinstance(task, dict) else None
                if isinstance(value, bool) or value is None:
                    raise ValueError('missing or invalid estimated_cost_usd')
                cost = Decimal(str(value))
                if not cost.is_finite() or cost < 0:
                    raise ValueError('missing or invalid estimated_cost_usd')
                total += cost
            except (InvalidOperation, ValueError):
                errors.append({'index': index, 'reason': 'missing or invalid estimated_cost_usd'})
        for reason in result['errors']:
            errors.append({'index': index, 'reason': reason})
        if isinstance(task, dict) and isinstance(task.get('id'), str) and task['id'].strip():
            canonical_id = task['id'].strip()
            if task['id'] != canonical_id:
                errors.append({'index': index, 'reason': 'task id must be canonical (no surrounding whitespace)'})
            if canonical_id in seen:
                errors.append({'index': index, 'reason': 'duplicate task id'})
            seen.add(canonical_id)
    if budget_usd is not None and total > limit:
        errors.append({'index': None, 'reason': 'estimated batch cost exceeds budget'})
    if errors:
        return {'valid': False, 'plans': [], 'errors': errors}
    return {'valid': True, 'plans': [make_execution_plan(task) for task in tasks], 'errors': []}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Offline synthetic-only CODEN review queue (never executes tasks)')
    parser.add_argument('input', help='Path to JSON array of synthetic tasks')
    parser.add_argument('--budget-usd', help='Optional nonnegative batch estimate ceiling; requires estimated_cost_usd on every task')
    args = parser.parse_args(argv)
    try:
        tasks = json.loads(Path(args.input).read_text(encoding='utf-8'))
        result = prepare_review_queue(tasks, budget_usd=args.budget_usd)
    except (OSError, UnicodeError, ValueError) as exc:
        result = {'valid': False, 'plans': [], 'errors': [{'index': None, 'reason': type(exc).__name__}]}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result['valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
