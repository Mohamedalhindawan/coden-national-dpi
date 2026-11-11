"""Offline synthetic tests for live upstream drift detection."""
import unittest
from scripts import check_kpi_upstream_drift as drift

class KpiUpstreamDriftTests(unittest.TestCase):
    def test_matching_blob(self):
        calls = []
        def fetch(url, token):
            calls.append(url)
            if "/pulls/" in url:
                return {"head": {"sha": "a" * 40, "repo": {"full_name": drift.REPO}}}
            return {"sha": drift.EXPECTED}
        self.assertEqual(drift.check(fetch=fetch)[1], drift.EXPECTED)
        self.assertIn("ref=" + "a" * 40, calls[1])

    def test_detects_upstream_change(self):
        def fetch(url, token):
            if "/pulls/" in url:
                return {"head": {"sha": "a" * 40, "repo": {"full_name": drift.REPO}}}
            return {"sha": "b" * 40}
        with self.assertRaisesRegex(ValueError, "schema drift"):
            drift.check(fetch=fetch)

    def test_missing_head_fails_closed(self):
        def fetch(url, token):
            return {"head": {"sha": "", "repo": {"full_name": drift.REPO}}}
        with self.assertRaisesRegex(ValueError, "Missing upstream"):
            drift.check(fetch=fetch)

    def test_api_failure_propagates(self):
        def fetch(url, token):
            raise RuntimeError("rate limited")
        with self.assertRaisesRegex(RuntimeError, "rate limited"):
            drift.check(fetch=fetch)

if __name__ == "__main__":
    unittest.main()
