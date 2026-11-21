"""Deterministic, offline, non-executing provider recovery recommendations.

This policy never invokes an API, refreshes credentials, moves subscription
cookies, grants approval or starts a task. All candidates require independent
human review and authorization before *any* actual execution.
"""

from decimal import Decimal, InvalidOperation
import re

LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z")
FAILURES = frozenset({
    'quota_exceeded', 'rate_limited', 'context_exceeded', 'provider_unavailable',
    'worker_failed', 'budget_exceeded', 'authentication_failed', 'policy_denied',
    'unknown',
})
FALLBACK_KINDS = frozenset({'quota_exceeded', 'rate_limited', 'provider_unavailable'})
HTTP_KINDS = {401: 'authentication_failed', 403: 'authentication_failed',
              413: 'context_exceeded', 429: 'rate_limited',
              502: 'provider_unavailable', 503: 'provider_unavailable',
              504: 'provider_unavailable'}
TASK_KEYS = frozenset({'classification', 'required_capabilities', 'budget_remaining_usd',
                       'allowed_providers', 'allow_external_api'})
ROUTE_KEYS = frozenset({'provider_id', 'model_id', 'transport', 'enabled', 'approved',
                        'capabilities', 'data_classes', 'estimated_cost_usd'})
MAX_ROUTES = 32


def _label(value):
    if not isinstance(value, str) or not LABEL.fullmatch(value):
        raise ValueError('invalid identifier')
    return value


def _tags(value):
    if not isinstance(value, list) or not 1 <= len(value) <= 16:
        raise ValueError('invalid identifier list')
    labels = [_label(x) for x in value]
    if len(labels) != len(set(labels)):
        raise ValueError('duplicate identifier')
    return frozenset(labels)


def _money(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError('invalid cost')
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError('invalid cost') from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError('invalid cost')
    return amount


def classify_failure(observation):
    """Accept only sanitized adapter error codes/status; never inspect messages."""
    if not isinstance(observation, dict) or not observation or set(observation) - {'kind', 'http_status'}:
        raise ValueError('invalid structured failure observation')
    kind = observation.get('kind')
    status = observation.get('http_status')
    if kind is not None and (not isinstance(kind, str) or kind not in FAILURES):
        raise ValueError('unsupported failure kind')
    if status is not None and (type(status) is not int or status < 100 or status > 599):
        raise ValueError('invalid HTTP status')
    inferred = HTTP_KINDS.get(status, 'unknown') if status is not None else None
    if kind is not None and inferred not in (None, 'unknown', kind):
        raise ValueError('conflicting failure evidence')
    return kind or inferred or 'unknown'


def _task(task):
    if not isinstance(task, dict) or set(task) != TASK_KEYS:
        raise ValueError('invalid task policy')
    if task['classification'] != 'synthetic':
        raise ValueError('only synthetic tasks supported')
    if type(task['allow_external_api']) is not bool:
        raise ValueError('invalid external API permission')
    return {
        'capabilities': _tags(task['required_capabilities']),
        'budget': _money(task['budget_remaining_usd']),
        'allowed': _tags(task['allowed_providers']),
        'external': task['allow_external_api'],
    }


def _routes(routes):
    if not isinstance(routes, list) or len(routes) > MAX_ROUTES:
        raise ValueError('invalid route registry')
    seen = set()
    checked = []
    for route in routes:
        if not isinstance(route, dict) or set(route) != ROUTE_KEYS:
            raise ValueError('invalid route fields')
        provider = _label(route['provider_id'])
        model = _label(route['model_id'])
        identity = (provider, model)
        if identity in seen:
            raise ValueError('duplicate route')
        seen.add(identity)
        if route['transport'] not in ('local', 'official_api_key'):
            raise ValueError('non-approved authentication transport')
        if type(route['enabled']) is not bool or type(route['approved']) is not bool:
            raise ValueError('invalid approval flag')
        checked.append({
            'provider_id': provider,
            'model_id': model,
            'transport': route['transport'],
            'enabled': route['enabled'],
            'approved': route['approved'],
            'capabilities': _tags(route['capabilities']),
            'data_classes': _tags(route['data_classes']),
            'cost': _money(route['estimated_cost_usd']),
        })
    return checked


def _decision(failure, decision, reason, next_action, candidate=None):
    return {
        'failure': failure, 'decision': decision, 'reason': reason,
        'next_action': next_action, 'candidate': candidate,
        'execution_authorized': False, 'requires_human_review': True,
    }


def plan_recovery(observation, task, routes, *, failed_provider=None):
    """Return a *proposal* only, never a command or authorization."""
    failure = classify_failure(observation)
    request = _task(task)
    candidates = _routes(routes)  # Check all entries, even ones not selected.
    if failed_provider is not None:
        _label(failed_provider)
    if failure in ('budget_exceeded', 'authentication_failed', 'policy_denied', 'unknown'):
        return _decision(failure, 'blocked', 'requires_operator_investigation', 'manual_security_review')
    if failure == 'context_exceeded':
        return _decision(failure, 'pause', 'context_rework_required', 'reduce_context')
    if failure == 'worker_failed':
        return _decision(failure, 'pause', 'worker_check_required', 'inspect_worker')
    if failure not in FALLBACK_KINDS:
        return _decision(failure, 'blocked', 'unsupported_error', 'manual_security_review')
    eligible = [r for r in candidates if r['enabled'] and r['approved']
                and r['provider_id'] in request['allowed']
                and r['provider_id'] != failed_provider
                and 'synthetic' in r['data_classes']
                and request['capabilities'].issubset(r['capabilities'])
                and r['cost'] <= request['budget']
                and (r['transport'] == 'local' or request['external'])]
    if not eligible:
        return _decision(failure, 'pause', 'no_authorized_route', 'wait_for_authorized_provider')
    eligible.sort(key=lambda r: (r['transport'] != 'local', r['cost'], r['provider_id'], r['model_id']))
    choice = eligible[0]
    return _decision(failure, 'propose_fallback', 'eligible_route_for_review', 'review_fallback',
                     {'provider_id': choice['provider_id'], 'model_id': choice['model_id'],
                      'transport': choice['transport'], 'estimated_cost_usd': str(choice['cost'])})
