import json
import unittest
from ai_factory.factory_qwen_tool_benchmark import CASES, request_for, audit_case, summarize


def reply(name, args):
    return json.dumps({"choices":[{"finish_reason":"tool_calls","message":{"role":"assistant","content":None,"tool_calls":[{"id":"call_test","type":"function","function":{"name":name,"arguments":json.dumps(args)}}]}}],"usage":{"completion_tokens":22}}).encode()


class ToolBenchmarkTests(unittest.TestCase):
    def test_cases_use_distinct_tools_and_automatic_choice(self):
        self.assertGreaterEqual(len({case["expected_tool"] for case in CASES.values()}), 3)
        for case_id, case in CASES.items():
            req = request_for(case_id)
            self.assertEqual(req["tool_choice"], "auto")
            self.assertEqual(len(req["tools"]), 3)
            self.assertNotIn(case["expected_tool"], req["messages"][0]["content"])

    def test_exact_expected_arguments_for_each_case(self):
        for case_id, case in CASES.items():
            self.assertEqual(audit_case(case_id, reply(case["expected_tool"],case["expected_args"]))["status"], "schema_match")

    def test_wrong_tool_and_bool_integer_substitution_rejected(self):
        case = CASES["limit"]
        self.assertEqual(audit_case("limit", reply("count_flags",case["expected_args"]))["status"], "schema_rejected")
        self.assertEqual(audit_case("limit", reply(case["expected_tool"],{"limit":True}))["status"], "schema_rejected")

    def test_missing_case_cannot_pass_benchmark(self):
        self.assertEqual(summarize({})["status"], "benchmark_rejected")

    def test_summary_requires_all_cases_and_no_execution(self):
        result = summarize({i:audit_case(i,reply(c["expected_tool"],c["expected_args"])) for i,c in CASES.items()})
        self.assertEqual(result["status"], "benchmark_match")
        self.assertFalse(result["tool_executed"])
        self.assertFalse(result["release_authorized"])
