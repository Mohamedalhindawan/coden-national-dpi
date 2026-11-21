"""Research-only CODEN component inventory is never an activation manifest."""
import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit


FILE = Path(__file__).resolve().parents[1] / "configs" / "factory_components_proposed.json"


class ComponentCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(FILE.read_text(encoding="utf-8"))

    def test_all_candidates_have_unique_identifiers(self):
        candidates = self.data["candidates"]
        self.assertEqual(len(candidates), 16)
        ids = [c["id"] for c in candidates]
        self.assertEqual(len(ids), len(set(ids)))

    def test_no_candidate_is_installed_or_approved(self):
        self.assertEqual(self.data["status"], "research_only")
        self.assertFalse(self.data["production_deploy_enabled"])
        self.assertFalse(self.data["provider_quota_bypass_allowed"])
        for c in self.data["candidates"]:
            with self.subTest(id=c["id"]):
                self.assertEqual(c["status"], "not_installed")
                self.assertFalse(c["approved"])
                self.assertFalse(c["enabled"])
                self.assertEqual(c["license_review"], "required")
                self.assertEqual(c["security_review"], "required")
                self.assertEqual(c["integration_test"], "not_run")

    def test_all_urls_are_upstream_https_github_repositories(self):
        for c in self.data["candidates"]:
            with self.subTest(id=c["id"]):
                p = urlsplit(c["upstream"])
                self.assertEqual(p.scheme, "https")
                self.assertEqual(p.netloc, "github.com")
                self.assertEqual(len([x for x in p.path.split("/") if x]), 2)
                self.assertFalse(p.query or p.fragment or p.username or p.password)

    def test_no_credentials_or_provider_auth_in_catalog(self):
        forbidden = ("api_key", "token", "cookie", "password", "secret", "oauth")
        for c in self.data["candidates"]:
            self.assertFalse(any(term in c for term in forbidden))
        self.assertTrue(self.data["user_approval_required"])


if __name__ == "__main__":
    unittest.main()
