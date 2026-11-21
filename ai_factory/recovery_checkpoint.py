"""Persist an offline provider-failure recommendation into the existing journal.

The adapter accepts only sanitized errors, policy data and provider metadata.
It does not run a model, approve a fallback or consume a provider quota.
"""

from . import checkpoint, recovery_policy


def record_recovery(store, task_id, observation, task, routes, *, failed_provider=None, event_key=None):
    """Plan fail-closed recovery and persist only a safe next-action identifier."""
    plan = recovery_policy.plan_recovery(observation, task, routes, failed_provider=failed_provider)
    kind = plan['failure']
    journal_event = 'blocked' if plan['decision'] == 'blocked' else kind
    state = checkpoint.record(store, task_id, event=journal_event,
                              next_action=plan['next_action'], event_key=event_key)
    return {'plan': plan, 'journal': state}
