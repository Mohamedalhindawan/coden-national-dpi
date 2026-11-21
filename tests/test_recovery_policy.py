"""Offline fail-closed recovery planning: no model calls or credentials."""
import unittest
from ai_factory import recovery_policy


def task(**changes):
    base = {
        'classification': 'synthetic',
        'required_capabilities': ['coding', 'tool_calls'],
        'budget_remaining_usd': '0',
        'allowed_providers': ['local_qwen', 'cloud_a'],
        'allow_external_api': False,
    }
    return dict(base, **changes)


def route(provider='local_qwen', model='qwen_local', **changes):
    base = {
        'provider_id': provider,
        'model_id': model,
        'transport': 'local',
        'enabled': True,
        'approved': True,
        'capabilities': ['coding', 'tool_calls'],
        'data_classes': ['synthetic'],
        'estimated_cost_usd': '0',
    }
    return dict(base, **changes)


class RecoveryPolicyTests(unittest.TestCase):
    def test_classify_quota_by_exact_code(self):
        self.assertEqual(recovery_policy.classify_failure({'kind': 'quota_exceeded'}), 'quota_exceeded')
        self.assertEqual(recovery_policy.classify_failure({'http_status': 429}), 'rate_limited')
        self.assertEqual(recovery_policy.classify_failure({'http_status': 413}), 'context_exceeded')
        self.assertEqual(recovery_policy.classify_failure({'http_status': 503}), 'provider_unavailable')
        self.assertEqual(recovery_policy.classify_failure({'http_status': 401}), 'authentication_failed')
        self.assertEqual(recovery_policy.classify_failure({'http_status': 400}), 'unknown')

    def test_reject_raw_secret_or_text_in_error_observation(self):
        with self.assertRaises(ValueError):
            recovery_policy.classify_failure({'kind': 'quota_exceeded', 'message': 'token=secret'})
        with self.assertRaises(ValueError):
            recovery_policy.classify_failure({'kind': 'QUOTA_EXCEEDED; run this'})
        with self.assertRaises(ValueError):
            recovery_policy.classify_failure({'http_status': True})

    def test_quota_proposes_only_approved_local_alternative(self):
        result = recovery_policy.plan_recovery(
            {'kind': 'quota_exceeded'}, task(),
            [route(), route('cloud_a', 'cloud_model', transport='official_api_key',
                             estimated_cost_usd='0.02')],
            failed_provider='codex_sub',
        )
        self.assertEqual(result['decision'], 'propose_fallback')
        self.assertEqual(result['candidate']['provider_id'], 'local_qwen')
        self.assertFalse(result['execution_authorized'])
        self.assertTrue(result['requires_human_review'])
        self.assertEqual(result['next_action'], 'review_fallback')

    def test_no_approved_alternative_pauses_safely(self):
        r = recovery_policy.plan_recovery({'kind': 'quota_exceeded'}, task(),
            [route(enabled=False), route('cloud_a', 'x', transport='official_api_key',
                                         estimated_cost_usd='0')], failed_provider='codex_sub')
        self.assertEqual(r['decision'], 'pause')
        self.assertIsNone(r['candidate'])

    def test_excludes_failed_provider_even_with_other_model(self):
        r = recovery_policy.plan_recovery({'kind': 'quota_exceeded'}, task(),
            [route(), route('local_qwen', 'different')], failed_provider='local_qwen')
        self.assertEqual(r['decision'], 'pause')

    def test_non_synthetic_data_fail_closed(self):
        with self.assertRaises(ValueError):
            recovery_policy.plan_recovery({'kind': 'quota_exceeded'}, task(classification='citizen'), [route()])

    def test_external_api_requires_explicit_permission_and_budget(self):
        cloud = route('cloud_a', 'paid', transport='official_api_key', estimated_cost_usd='0.05')
        out = recovery_policy.plan_recovery({'kind': 'quota_exceeded'}, task(
            allow_external_api=False, budget_remaining_usd='1'), [cloud])
        self.assertEqual(out['decision'], 'pause')
        out = recovery_policy.plan_recovery({'kind': 'quota_exceeded'}, task(
            allow_external_api=True, budget_remaining_usd='0'), [cloud])
        self.assertEqual(out['decision'], 'pause')
        out = recovery_policy.plan_recovery({'kind': 'quota_exceeded'}, task(
            allow_external_api=True, budget_remaining_usd='0.05'), [cloud])
        self.assertEqual(out['decision'], 'propose_fallback')
        self.assertFalse(out['execution_authorized'])

    def test_never_use_unapproved_or_unauthorized_routes(self):
        routes = [route(approved=False), route('other', 'alternate')]
        r = recovery_policy.plan_recovery({'kind':'quota_exceeded'}, task(), routes)
        self.assertEqual(r['decision'], 'pause')

    def test_capabilities_and_data_classes_required(self):
        cases = [route(capabilities=['coding']), route(data_classes=['internal'])]
        for candidate in cases:
            with self.subTest(candidate=candidate):
                r = recovery_policy.plan_recovery({'kind':'quota_exceeded'}, task(), [candidate])
                self.assertEqual(r['decision'], 'pause')

    def test_budget_or_auth_or_policy_failure_never_proposes(self):
        for kind in ('budget_exceeded', 'authentication_failed', 'policy_denied', 'unknown'):
            with self.subTest(kind=kind):
                r = recovery_policy.plan_recovery({'kind':kind}, task(), [route()])
                self.assertEqual(r['decision'], 'blocked')
                self.assertIsNone(r['candidate'])

    def test_context_failure_requires_context_rework_not_model_swap(self):
        r = recovery_policy.plan_recovery({'kind':'context_exceeded'}, task(), [route()])
        self.assertEqual(r['decision'], 'pause')
        self.assertEqual(r['next_action'], 'reduce_context')

    def test_worker_failure_requires_manual_recovery(self):
        r = recovery_policy.plan_recovery({'kind':'worker_failed'}, task(), [route()])
        self.assertEqual(r['decision'], 'pause')
        self.assertEqual(r['next_action'], 'inspect_worker')

    def test_deterministic_candidate_order_is_local_first(self):
        r = recovery_policy.plan_recovery({'kind':'provider_unavailable'}, task(
            allow_external_api=True, budget_remaining_usd='1'), [
                route('cloud_a', 'paid', transport='official_api_key', estimated_cost_usd='0'),
                route('local_qwen', 'local', estimated_cost_usd='0')])
        self.assertEqual(r['candidate']['provider_id'], 'local_qwen')

    def test_reject_ambiguous_or_dangerous_registry(self):
        bads = [
            route(transport='subscription_cookie'),
            route(estimated_cost_usd='NaN'),
            route(estimated_cost_usd='-1'),
            route(provider_id='../escape'),
            route(model_id='danger\n'),
            route(approved=1),
            route(api_key='secret'),
        ]
        for bad in bads:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                recovery_policy.plan_recovery({'kind':'quota_exceeded'}, task(), [bad])

    def test_invalid_budget_and_duplicate_routes_rejected(self):
        with self.assertRaises(ValueError):
            recovery_policy.plan_recovery({'kind':'quota_exceeded'}, task(budget_remaining_usd='Infinity'), [route()])
        with self.assertRaises(ValueError):
            recovery_policy.plan_recovery({'kind':'quota_exceeded'}, task(), [route(), route()])


if __name__ == '__main__':
    unittest.main()
