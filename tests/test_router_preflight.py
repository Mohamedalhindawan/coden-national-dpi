import unittest
from ai_factory.router_preflight import check_router_config

class RouterPreflightTests(unittest.TestCase):
    def test_safe_local_config(self):
        self.assertEqual(check_router_config({'base_url':'http://127.0.0.1:3001/v1','api_style':'responses','model':'demo-model'})['errors'],[])
    def test_rejects_remote_and_wildcard_hosts(self):
        for host in ['https://router.example/v1','http://0.0.0.0:3001/v1','http://localhost.evil.com/v1']:
            with self.subTest(host=host): self.assertFalse(check_router_config({'base_url':host,'api_style':'responses','model':'x'})['ready'])
    def test_rejects_credentials_in_url(self):
        self.assertFalse(check_router_config({'base_url':'http://token:secret@localhost:3001/v1','api_style':'responses','model':'x'})['ready'])
    def test_requires_responses_and_model(self):
        self.assertFalse(check_router_config({'base_url':'http://localhost:3001/v1','api_style':'chat_completions','model':'x'})['ready'])
        self.assertFalse(check_router_config({'base_url':'http://localhost:3001/v1','api_style':'responses','model':''})['ready'])
    def test_never_echoes_secret(self):
        result=check_router_config({'base_url':'http://localhost:3001/v1','api_style':'responses','model':'x','api_key':'SENSITIVE_TOKEN'})
        self.assertNotIn('SENSITIVE_TOKEN',repr(result))
        self.assertFalse(result['ready'])
    def test_bad_type(self):
        self.assertFalse(check_router_config(None)['ready'])
