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

    def test_local_http_receipt_rejects_auth_timeout_cancel_and_wrong_model(self):
        from ai_factory import factory_qwen_tool_benchmark as bench
        response = json.loads(reply("count_flags", CASES["count"]["expected_args"]))
        response["model"] = "local-qwen"
        raw = json.dumps(response).encode()
        accepted = bench.audit_http_case("count", status_code=200, raw=raw)
        self.assertEqual(accepted["status"], "schema_match")
        self.assertFalse(accepted["tool_executed"])
        self.assertFalse(accepted["sdk_conversation_ran"])
        self.assertFalse(accepted["release_authorized"])
        for code, failure, reason in (
            (401, None, "authentication_failed"),
            (403, None, "authentication_failed"),
            (302, None, "http_status_rejected"),
            (429, None, "http_status_rejected"),
            (200, "timeout", "timeout"),
            (200, "cancelled", "cancelled"),
            (200, "unknown", "invalid_transport_outcome"),
        ):
            with self.subTest(code=code, failure=failure):
                result = bench.audit_http_case("count", status_code=code, raw=raw, failure=failure)
                self.assertEqual(result["status"], "schema_rejected")
                self.assertEqual(result["reason_code"], reason)
                self.assertFalse(result["automatic_retry_allowed"])
                self.assertFalse(result["release_authorized"])
                self.assertNotIn("response_sha256", result)
        response["model"] = "private-unexpected-model"
        result = bench.audit_http_case("count", status_code=200, raw=json.dumps(response).encode())
        self.assertEqual(result["reason_code"], "model_identity_mismatch")
        self.assertNotIn("private-unexpected-model", repr(result))
        self.assertFalse(result["automatic_retry_allowed"])

    def test_captured_benchmark_cli_rejects_wrong_or_missing_model_alias(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from ai_factory import factory_qwen_tool_benchmark as bench
        for alias in ("local-qwen", "unexpected-model", None):
            with self.subTest(alias=alias), TemporaryDirectory() as temp:
                folder = Path(temp)
                for case_id, case in CASES.items():
                    response = json.loads(reply(case["expected_tool"], case["expected_args"]))
                    if alias is not None:
                        response["model"] = alias
                    (folder / (case_id + ".json")).write_text(json.dumps(response))
                receipt = folder / "receipt.json"
                with patch.object(bench.sys, "argv", ["benchmark", "review", temp, str(receipt)]):
                    if alias == "local-qwen":
                        bench.main()
                    else:
                        with self.assertRaises(SystemExit):
                            bench.main()
                result = json.loads(receipt.read_text())
                self.assertEqual(result["status"], "benchmark_match" if alias == "local-qwen" else "benchmark_rejected")
                self.assertFalse(result["release_authorized"])
                self.assertFalse(result["sdk_conversation_ran"])
                if alias != "local-qwen":
                    self.assertTrue(all(v["reason_code"] == "model_identity_mismatch" for v in result["cases"].values()))
                    self.assertNotIn("unexpected-model", repr(result))

    def test_http_capture_rejects_nonstandard_json_constants(self):
        from ai_factory import factory_qwen_tool_benchmark as bench
        response = json.loads(reply("count_flags", CASES["count"]["expected_args"]))
        response["model"] = "local-qwen"
        for constant in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(constant=constant):
                response["untrusted_extra"] = constant
                result = bench.audit_http_case("count", status_code=200,
                                              raw=json.dumps(response).encode())
                self.assertEqual(result["status"], "schema_rejected")
                self.assertEqual(result["reason_code"], "invalid_json")
                self.assertFalse(result["automatic_retry_allowed"])
                self.assertFalse(result["release_authorized"])
                self.assertNotIn("response_sha256", result)


class QwenPreflightBrokerTests(unittest.TestCase):
    TOKEN = b"synthetic-fixture-token-not-a-real-credential"
    def make(self, **kwargs):
        import hashlib
        from ai_factory.factory_qwen_tool_benchmark import PreflightBroker
        return PreflightBroker(token_sha256=hashlib.sha256(self.TOKEN).hexdigest(),
                               case_id="count", ttl_seconds=30, **kwargs)

    def transport(self, **kw):
        self.assertEqual(kw["url"], "http://qwen3:11434/v1/chat/completions")
        self.assertEqual(kw["timeout_seconds"], 35)
        self.assertEqual(kw["max_response_bytes"], 256*1024)
        self.assertEqual(kw["request"], request_for("count"))
        self.assertNotIn("token", kw)
        body=json.loads(reply("count_flags",CASES["count"]["expected_args"]))
        body["model"]="local-qwen"
        return 200,json.dumps(body).encode()

    def test_one_shot_authenticated_fixture_rejects_wrong_token_and_replay(self):
        from unittest.mock import Mock
        broker=self.make()
        send=Mock(side_effect=self.transport)
        result=broker.execute(token=b"wrong",fixture_only=True,transport=send)
        self.assertEqual(result["status"],"authentication_failed")
        send.assert_not_called()
        result=broker.execute(token=self.TOKEN,fixture_only=True,transport=send)
        self.assertEqual(result["status"],"fixture_preflight_match")
        self.assertFalse(result["qwen_connected"])
        self.assertFalse(result["execution_authorized"])
        self.assertNotIn(self.TOKEN.decode(),repr(result))
        self.assertEqual(broker.execute(token=self.TOKEN,fixture_only=True,transport=send)["status"],"grant_consumed")
        send.assert_called_once()

    def test_real_transport_blocked_and_expiry_precedes_dispatch(self):
        from unittest.mock import Mock,patch
        from ai_factory import factory_qwen_tool_benchmark as bench
        send=Mock(side_effect=self.transport)
        with patch.object(bench.time,"monotonic",return_value=100):
            broker=self.make()
        with patch.object(bench.time,"monotonic",return_value=101):
            self.assertEqual(broker.execute(token=self.TOKEN,transport=send)["status"],"blocked_runtime_admission")
        with patch.object(bench.time,"monotonic",return_value=130):
            self.assertEqual(broker.execute(token=self.TOKEN,fixture_only=True,transport=send)["status"],"grant_expired")
        send.assert_not_called()

    def test_failure_consumes_grant_without_leaking_transport_error(self):
        from unittest.mock import Mock
        for status in (401,403,429,500,302,200):
            with self.subTest(status=status):
                broker=self.make()
                send=Mock(return_value=(status,b"private-response"*30000))
                result=broker.execute(token=self.TOKEN,fixture_only=True,transport=send)
                self.assertNotEqual(result["status"],"fixture_preflight_match")
                self.assertNotIn("private-response",repr(result))
                self.assertEqual(broker.execute(token=self.TOKEN,fixture_only=True,transport=send)["status"],"grant_consumed")
                send.assert_called_once()
        broker=self.make()
        send=Mock(side_effect=RuntimeError("private-transport-error"))
        result=broker.execute(token=self.TOKEN,fixture_only=True,transport=send)
        self.assertEqual(result["status"],"fixture_transport_failed")
        self.assertNotIn("private",repr(result))

    def test_cancelled_and_concurrent_claim_cannot_dispatch_twice(self):
        from unittest.mock import Mock
        from concurrent.futures import ThreadPoolExecutor
        broker=self.make()
        send=Mock(side_effect=self.transport)
        result=broker.execute(token=self.TOKEN,fixture_only=True,transport=send,cancelled=lambda:True)
        self.assertEqual(result["status"],"cancelled")
        send.assert_not_called()
        self.assertEqual(broker.execute(token=self.TOKEN,fixture_only=True,transport=send)["status"],"grant_consumed")
        broker=self.make()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:broker.execute(token=self.TOKEN,fixture_only=True,transport=send),range(2)))
        self.assertEqual(sorted(r["status"] for r in results),["fixture_preflight_match","grant_consumed"])
        send.assert_called_once()
