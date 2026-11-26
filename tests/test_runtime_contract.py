"""Provider-neutral *metadata* contract: no LLM/network/API execution."""
import copy
import unittest
from ai_factory import runtime_contract


def request(**changes):
    req = {
        "schema": "coden.runtime.request.v1",
        "task_id": "demo_1",
        "task_sha256": "a" * 64,
        "classification": "synthetic",
        "required_capabilities": ["coding", "tool_calls"],
        "allowed_providers": ["local_qwen"],
        "allow_external_api": False,
        "max_tokens_total": 2048,
        "max_duration_seconds": 90,
        "max_cost_usd": "0",
    }
    return dict(req, **changes)


def report(**changes):
    res = {
        "schema": "coden.runtime.report.v1",
        "task_id": "demo_1",
        "provider_id": "local_qwen",
        "model_id": "qwen_local",
        "transport": "local",
        "status": "completed",
        "error_code": None,
        "artifact_sha256": "b" * 64,
        "input_tokens": 300,
        "output_tokens": 400,
        "duration_ms": 2500,
        "cost_usd": "0",
    }
    return dict(res, **changes)


class RuntimeContractTests(unittest.TestCase):
    def test_valid_bounded_synthetic_report_never_approves_execution(self):
        result = runtime_contract.assess(request(), report())
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["contract_valid"])
        self.assertTrue(result["artifact_hash_recorded"])
        self.assertFalse(result["artifact_verified"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["provider_approved"])

    def test_refuses_raw_prompt_and_credentials_in_request_or_report(self):
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(prompt="private data"), report())
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(), report(api_key="secret"))
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(), report(raw_output="secret"))
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(approval=True), report())

    def test_rejects_non_synthetic_data_and_external_transport_without_permission(self):
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(classification="citizen"), report())
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(), report(transport="official_api_key"))

    def test_provider_must_be_on_task_allowlist(self):
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(), report(provider_id="unapproved"))
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(allowed_providers=["another"]), report())

    def test_mismatched_task_identity_and_wrong_schema_rejected(self):
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(), report(task_id="other_task"))
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(schema="bad"), report())
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(), report(schema="bad"))

    def test_artifact_hash_cannot_be_treated_as_verified_file(self):
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(), report(artifact_sha256="not-a-hash"))
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(), report(artifact_sha256=None))
        outcome = runtime_contract.assess(request(), report())
        self.assertFalse(outcome["artifact_verified"])

    def test_failed_run_requires_sanitized_error_and_no_artifact(self):
        result = runtime_contract.assess(request(), report(
            status="failed", error_code="provider_unavailable", artifact_sha256=None))
        self.assertEqual(result["status"], "failed")
        self.assertFalse(result["artifact_hash_recorded"])
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(), report(status="failed", error_code=None, artifact_sha256=None))
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(), report(status="failed", error_code="secret-token", artifact_sha256=None))
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(), report(status="completed", error_code="quota_exceeded"))

    def test_token_time_and_cost_budget_are_hard_bounds(self):
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(), report(output_tokens=2000))
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(), report(duration_ms=90001))
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(), report(cost_usd="0.01"))

    def test_rejects_negative_boolean_nan_and_malformed_usage(self):
        for altered in (
            {"input_tokens": -1}, {"input_tokens": True},
            {"output_tokens": -1}, {"duration_ms": -2},
            {"cost_usd": "NaN"}, {"cost_usd": "-3"},
            {"cost_usd": True}, {"model_id": "../host"}
        ):
            with self.subTest(altered=altered), self.assertRaises(ValueError):
                runtime_contract.assess(request(), report(**altered))

    def test_rejects_unknown_status_or_cookie_auth_transport(self):
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(), report(status="approved"))
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(), report(transport="subscription_cookie"))

    def test_rejects_duplicate_capability_tags_and_invalid_budgets(self):
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(required_capabilities=["coding", "coding"]), report())
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(max_cost_usd="Infinity"), report())
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(max_tokens_total=0), report())
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(allow_external_api="true"), report())

    def test_approved_api_can_be_described_but_not_executed(self):
        r = runtime_contract.assess(
            request(allow_external_api=True, allowed_providers=["approved_api"], max_cost_usd="0.05"),
            report(provider_id="approved_api", transport="official_api_key", cost_usd="0.05"))
        self.assertTrue(r["contract_valid"])
        self.assertFalse(r["execution_authorized"])
        self.assertFalse(r["provider_approved"])

    def test_unhashable_report_status_and_error_are_rejected_cleanly(self):
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(), report(status=[]))
        with self.assertRaises(ValueError):
            runtime_contract.assess(request(), report(status="failed", error_code={},
                                                      artifact_sha256=None))


    def test_bound_local_report_requires_exact_request_and_model(self):
        import hashlib
        import json
        req = request()
        digest = hashlib.sha256(json.dumps(req, sort_keys=True, separators=(",", ":"),
                                          ensure_ascii=True).encode("ascii")).hexdigest()
        evidence = report(schema="coden.runtime.bound_report.v1", request_sha256=digest)
        result = runtime_contract.assess_bound_local(req, evidence, expected_model_id="qwen_local")
        self.assertTrue(result["request_digest_matches"])
        self.assertFalse(result["report_origin_verified"])
        self.assertFalse(result["artifact_verified"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["provider_approved"])
        for changed in (request(task_sha256="c"*64), request(max_tokens_total=4096)):
            with self.assertRaises(ValueError):
                runtime_contract.assess_bound_local(changed, evidence, expected_model_id="qwen_local")
        with self.assertRaises(ValueError):
            runtime_contract.assess_bound_local(req, evidence, expected_model_id="other_model")

    def test_bound_local_report_never_accepts_external_or_positive_cost_scope(self):
        import hashlib
        import json
        for req in (request(allow_external_api=True), request(max_cost_usd="0.01"),
                    request(allowed_providers=["local_qwen", "fallback"])):
            digest = hashlib.sha256(json.dumps(req, sort_keys=True, separators=(",", ":"),
                                              ensure_ascii=True).encode("ascii")).hexdigest()
            evidence = report(schema="coden.runtime.bound_report.v1", request_sha256=digest)
            with self.assertRaises(ValueError):
                runtime_contract.assess_bound_local(req, evidence, expected_model_id="qwen_local")


    def test_bound_json_receipt_is_validated_from_actual_wire_bytes(self):
        import hashlib
        import json
        req = request()
        digest = hashlib.sha256(json.dumps(req, sort_keys=True, separators=(",", ":"),
                                          ensure_ascii=True).encode("ascii")).hexdigest()
        # A fixture is not an inference run. Record only a blocked outcome.
        evidence = report(schema="coden.runtime.bound_report.v1", request_sha256=digest,
                          status="blocked", error_code="policy_denied", artifact_sha256=None,
                          input_tokens=0, output_tokens=0, duration_ms=0)
        raw = json.dumps(evidence, separators=(",", ":")).encode("utf-8")
        result = runtime_contract.assess_bound_local_json(req, raw, expected_model_id="qwen_local")
        self.assertTrue(result["request_digest_matches"])
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["artifact_hash_recorded"])
        self.assertFalse(result["report_origin_verified"])
        self.assertFalse(result["execution_authorized"])

    def test_bound_json_rejects_ambiguous_or_oversized_wire_data(self):
        import hashlib
        import json
        req = request()
        digest = hashlib.sha256(json.dumps(req, sort_keys=True, separators=(",", ":"),
                                          ensure_ascii=True).encode("ascii")).hexdigest()
        evidence = report(schema="coden.runtime.bound_report.v1", request_sha256=digest)
        raw = json.dumps(evidence, separators=(",", ":")).encode("utf-8")
        for invalid in (
            raw.replace(b'"status":', b'"status":"failed","status":', 1),
            raw.replace(b'"cost_usd":"0"', b'"cost_usd":NaN'),
            raw + b" " * 8193, raw + b"{}", b"\xff",
            b"["*5000 + b"0" + b"]"*5000, raw.decode("utf-8"),
        ):
            with self.subTest(kind=type(invalid).__name__), self.assertRaises(ValueError):
                runtime_contract.assess_bound_local_json(req, invalid, expected_model_id="qwen_local")



if __name__ == "__main__":
    unittest.main()
