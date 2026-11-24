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
