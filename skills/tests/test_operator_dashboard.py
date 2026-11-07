import unittest
from pathlib import Path


class OperatorDashboardAssetTests(unittest.TestCase):
    def test_dashboard_is_self_contained_accessible_and_uses_operator_api(self):
        path = Path(__file__).parents[1] / "orchestration" / "operator-dashboard" / "index.html"
        html = path.read_text(encoding="utf-8")
        for marker in ('lang="ar"', 'dir="rtl"', 'aria-live="polite"',
                       '/v1/workflows/status', '/v1/workflows/pause',
                       '/v1/workflows/resume', '/v1/workflows/dispatch',
                       '/v1/observability/snapshot', 'Authorization', 'loadMetrics'):
            self.assertIn(marker, html)
        self.assertNotIn("localStorage", html)
        self.assertNotIn("sessionStorage", html)
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)
        self.assertIn('id="reconciliationStatus"', html)
        self.assertIn('id="reconciliationObserved"', html)
        self.assertIn('id="reconciliationActual"', html)
        self.assertIn('id="reconciliationVariance"', html)
        self.assertIn('data.cost_reconciliation', html)
        self.assertIn('pending_linked_reservations', html)
        self.assertIn('/v1/finops/reconciliations', html)
        self.assertIn('finopsRequests', html)
        self.assertIn('finopsAudit', html)
        self.assertIn('decideFinops', html)
        self.assertIn('window.confirm', html)
