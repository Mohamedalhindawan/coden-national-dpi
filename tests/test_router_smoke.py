"""No-network smoke checks for optional Codex CLI router configuration."""
import unittest
from ai_factory.router_smoke import smoke_check


class RouterSmokeTests(unittest.TestCase):
    def test_valid_local_configuration(self):
        result = smoke_check({'CODEN_ROUTER_MODEL': 'demo-model'})
        self.assertTrue(result['ready'])

    def test_missing_model_is_not_ready(self):
        result = smoke_check({})
        self.assertFalse(result['ready'])
        self.assertIn('model must be a nonempty string', result['errors'])

    def test_external_host_is_not_ready(self):
        result = smoke_check({'CODEN_ROUTER_BASE_URL': 'https://example.org/v1', 'CODEN_ROUTER_MODEL': 'demo'})
        self.assertFalse(result['ready'])

    def test_secret_is_never_reported(self):
        result = smoke_check({'CODEN_ROUTER_MODEL': 'demo', 'CODEN_ROUTER_BASE_URL': 'http://user:SECRET@localhost:3001/v1'})
        self.assertNotIn('SECRET', repr(result))
