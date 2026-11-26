import copy
import unittest
from ai_factory.factory_qwen_tool_schema import audit_response


def response():
    return {"choices": [{"finish_reason": "tool_calls", "message": {
        "role": "assistant", "content": None, "tool_calls": [{
            "id": "call_synthetic", "type": "function",
            "function": {"name": "count_flags", "arguments": '{"flags":["pending","approved"]}'}
        }]
    }}], "usage": {"completion_tokens": 17}}


class ToolSchemaTests(unittest.TestCase):
    def test_accept_valid_structured_call_without_authorizing_execution(self):
        result = audit_response(response())
        self.assertEqual(result["status"], "schema_match")
        self.assertFalse(result["tool_executed"])
        self.assertFalse(result["release_authorized"])
        self.assertNotIn("arguments", result)

    def test_reject_plain_text_and_wrong_tool(self):
        for name in ("shell", "summarize_flags"):
            value = response()
            value["choices"][0]["message"]["tool_calls"][0]["function"]["name"] = name
            with self.assertRaises(ValueError):
                audit_response(value)
        value = response()
        value["choices"][0]["message"]["tool_calls"] = []
        with self.assertRaises(ValueError):
            audit_response(value)

    def test_reject_wrong_duplicate_or_extra_arguments(self):
        for raw in ('{"flags":["approved"]}', '{"flags":[],"flags":["pending","approved"]}', '{"flags":["pending","approved"],"command":"x"}'):
            value = response()
            value["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = raw
            with self.assertRaises(ValueError):
                audit_response(value)

    def test_reject_multiple_calls_or_missing_generated_tokens(self):
        value = response()
        value["choices"][0]["message"]["tool_calls"].append(copy.deepcopy(value["choices"][0]["message"]["tool_calls"][0]))
        with self.assertRaises(ValueError):
            audit_response(value)
        for count in (0, True, 129):
            value = response()
            value["usage"]["completion_tokens"] = count
            with self.assertRaises(ValueError):
                audit_response(value)

    def test_rejection_receipt_is_specific_without_untrusted_content(self):
        import json
        from ai_factory.factory_qwen_tool_schema import evaluate_response
        value = response()
        value["choices"][0]["finish_reason"] = "stop"
        value["choices"][0]["message"]["content"] = "synthetic-untrusted-text"
        verdict = evaluate_response(json.dumps(value).encode())
        self.assertEqual(verdict["status"], "schema_rejected")
        self.assertEqual(verdict["reason_code"], "finish_reason_or_role")
        self.assertNotIn("synthetic-untrusted-text", json.dumps(verdict))
        self.assertFalse(verdict["tool_executed"])
        self.assertFalse(verdict["release_authorized"])

    def test_invalid_json_diagnostic_does_not_echo_input(self):
        import json
        from ai_factory.factory_qwen_tool_schema import evaluate_response
        verdict = evaluate_response(b"not-json synthetic-untrusted-text")
        self.assertEqual(verdict["reason_code"], "invalid_json")
        self.assertNotIn("synthetic-untrusted-text", json.dumps(verdict))

    def test_success_receipt_has_response_digest_and_no_rejection(self):
        import hashlib
        import json
        from ai_factory.factory_qwen_tool_schema import evaluate_response
        raw = json.dumps(response()).encode()
        verdict = evaluate_response(raw)
        self.assertEqual(verdict["status"], "schema_match")
        self.assertEqual(verdict["response_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertNotIn("reason_code", verdict)
        self.assertFalse(verdict["tool_executed"])


    def test_cli_refuses_symlink_response_and_preserves_existing_receipt(self):
        import json
        import subprocess
        import sys
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.json"
            source.write_text(json.dumps(response()))
            alias = root / "alias.json"
            alias.symlink_to(source)
            receipt = root / "receipt.json"
            def run(src, dst):
                return subprocess.run([sys.executable, "-m", "ai_factory.factory_qwen_tool_schema",
                    str(src), str(dst)], capture_output=True, text=True, timeout=5)
            result = run(alias, receipt)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(receipt.exists())
            receipt.write_text("retained evidence")
            result = run(source, receipt)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(receipt.read_text(), "retained evidence")

    def test_cli_fresh_regular_input_produces_review_only_receipt(self):
        import json
        import subprocess
        import sys
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.json"
            source.write_text(json.dumps(response()))
            receipt = root / "receipt.json"
            result = subprocess.run([sys.executable, "-m", "ai_factory.factory_qwen_tool_schema",
                str(source), str(receipt)], capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(receipt.read_text())
            self.assertEqual(data["status"], "schema_match")
            self.assertFalse(data["tool_executed"])
            self.assertFalse(data["release_authorized"])
