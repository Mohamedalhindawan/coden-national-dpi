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
