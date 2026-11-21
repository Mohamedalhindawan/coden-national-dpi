"""Contract tests: only an explicitly opted-in loopback Ollama discovery GET."""
import http.server
import json
import threading
import unittest
from unittest.mock import MagicMock, patch

from ai_factory import ollama_probe

URL = "http://127.0.0.1:11434"
MODEL = "qwen2.5-coder:1.5b"


class OllamaAdmissionTests(unittest.TestCase):
    def test_disabled_by_default_and_no_network(self):
        with patch.object(ollama_probe.http.client, "HTTPConnection") as conn:
            result = ollama_probe.probe(URL, MODEL)
        conn.assert_not_called()
        self.assertEqual(result["probe_status"], "disabled")
        self.assertFalse(result["model_available"])
        self.assertFalse(result["probe_attempted"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["provider_approved"])

    def test_remote_urls_userinfo_paths_and_localhost_aliases_rejected_before_network(self):
        invalid = [
            "https://127.0.0.1:11434",
            "http://localhost:11434",
            "http://0.0.0.0:11434",
            "http://127.0.0.1.evil.net:11434",
            "http://user:secret@127.0.0.1:11434",
            "http://127.0.0.1:11434/v1",
            "http://127.0.0.1:11434?token=secret",
            "http://127.0.0.1:11434/#fragment",
            "http://127.0.0.1:0",
        ]
        with patch.object(ollama_probe.http.client, "HTTPConnection") as connection:
            for url in invalid:
                with self.subTest(url=url), self.assertRaises(ValueError):
                    ollama_probe.probe(url, MODEL, allow_loopback=True)
        connection.assert_not_called()

    def test_rejects_invalid_model_and_non_boolean_opt_in(self):
        for model in ("", "  ", "bad model", "model\nsecret", "a" * 130, None):
            with self.subTest(model=model), self.assertRaises(ValueError):
                ollama_probe.probe(URL, model)
        with self.assertRaises(ValueError):
            ollama_probe.probe(URL, MODEL, allow_loopback="yes")

    def _mock_response(self, *, status=200, payload=b'{"models":[{"name":"qwen2.5-coder:1.5b"}]}'):
        connection = MagicMock()
        response = connection.getresponse.return_value
        response.status = status
        response.read.return_value = payload
        return connection

    def test_success_queries_only_tags_and_does_not_authorize_execution(self):
        connection = self._mock_response()
        with patch.object(ollama_probe.http.client, "HTTPConnection", return_value=connection) as init:
            result = ollama_probe.probe(URL, MODEL, allow_loopback=True)
        init.assert_called_once_with("127.0.0.1", 11434, timeout=2)
        connection.request.assert_called_once_with("GET", "/api/tags", headers={"Accept": "application/json"})
        connection.close.assert_called_once()
        self.assertEqual(result["probe_status"], "available")
        self.assertTrue(result["probe_attempted"])
        self.assertTrue(result["model_available"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["provider_approved"])

    def test_model_not_installed_is_not_ready(self):
        with patch.object(ollama_probe.http.client, "HTTPConnection", return_value=self._mock_response()):
            result = ollama_probe.probe(URL, "other:latest", allow_loopback=True)
        self.assertEqual(result["probe_status"], "model_absent")
        self.assertFalse(result["model_available"])

    def test_http_error_is_sanitized_and_not_retried(self):
        connection = self._mock_response(status=503, payload=b"SECRET INTERNAL DATA")
        with patch.object(ollama_probe.http.client, "HTTPConnection", return_value=connection):
            result = ollama_probe.probe(URL, MODEL, allow_loopback=True)
        self.assertEqual(result["probe_status"], "http_error")
        self.assertFalse(result["model_available"])
        self.assertNotIn("SECRET", repr(result))
        connection.request.assert_called_once()

    def test_rejects_malformed_duplicate_and_oversize_response(self):
        payloads = (
            b"not json",
            b'{"models":{} }',
            b'{"models":[],"models":[{"name":"qwen2.5-coder:1.5b"}]}',
            b'{"models":[{"name":123}]}',
            b'{"models":[{"name":"qwen2.5-coder:1.5b"}]}' + b" " * (ollama_probe.MAX_RESPONSE_BYTES + 1),
        )
        for payload in payloads:
            with self.subTest(length=len(payload)):
                with patch.object(ollama_probe.http.client, "HTTPConnection",
                                  return_value=self._mock_response(payload=payload)):
                    result = ollama_probe.probe(URL, MODEL, allow_loopback=True)
                self.assertIn(result["probe_status"], ("invalid_response", "oversized_response"))
                self.assertFalse(result["model_available"])

    def test_connection_failure_does_not_leak_exception(self):
        with patch.object(ollama_probe.http.client, "HTTPConnection") as ctor:
            ctor.return_value.request.side_effect = OSError("sensitive local exception")
            result = ollama_probe.probe(URL, MODEL, allow_loopback=True)
        self.assertEqual(result["probe_status"], "unreachable")
        self.assertNotIn("sensitive", repr(result))
        self.assertFalse(result["execution_authorized"])

    def test_real_loopback_http_fixture_never_calls_a_model(self):
        class Models(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path != "/api/tags":
                    self.send_error(404)
                    return
                body = json.dumps({"models": [{"name": MODEL}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                pass

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Models)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            result = ollama_probe.probe(f"http://127.0.0.1:{server.server_port}",
                                        MODEL, allow_loopback=True)
            self.assertEqual(result["probe_status"], "available")
            self.assertTrue(result["model_available"])
            self.assertFalse(result["execution_authorized"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
