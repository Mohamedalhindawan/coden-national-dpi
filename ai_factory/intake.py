"""Synthetic-only CODEN engineering task intake and approval-gated plan.

No tool execution, network access, persistence, or approval is performed here.
"""

ALLOWED_ACTIONS = frozenset({'read_repository', 'write_branch', 'run_tests', 'draft_pull_request'})
REQUIRED = ('id', 'title', 'description', 'data_classification', 'requested_actions')


def validate_intake(task):
    errors = []
    if not isinstance(task, dict):
        return {'valid': False, 'errors': ['task must be an object']}
    for key in REQUIRED:
        if key not in task:
            errors.append(f'missing {key}')
    for key in ('id', 'title', 'description'):
        if key in task and (not isinstance(task[key], str) or not task[key].strip()):
            errors.append(f'invalid {key}')
    if task.get('data_classification') != 'synthetic':
        errors.append('only synthetic data is permitted')
    actions = task.get('requested_actions')
    if not isinstance(actions, list) or not actions:
        errors.append('requested_actions must be a nonempty list')
    elif any(not isinstance(a, str) or a not in ALLOWED_ACTIONS for a in actions):
        errors.append('requested_actions includes forbidden or unknown action')
    return {'valid': not errors, 'errors': errors}


def make_execution_plan(task):
    validation = validate_intake(task)
    if not validation['valid']:
        raise ValueError('; '.join(validation['errors']))
    return {
        'task_id': task['id'],
        'status': 'awaiting_human_approval',
        'execution_authorized': False,
        'steps': ['review_specification', 'prepare_isolated_branch', 'run_independent_tests', 'security_review', 'human_approval'],
        'requested_actions': list(task['requested_actions']),
        'data_classification': 'synthetic',
    }
