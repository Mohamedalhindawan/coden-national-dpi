"""Regression tests for safe failure diagnostics of the offline CPU pilot."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from ai_factory.factory_failure_diagnostic import summarize
from ai_factory.project import inspect_source


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "ai_factory/examples/factory-review-queue-metric.json"
WORKFLOW = ROOT / ".github/workflows/factory-self-improvement-cpu.yml"


class FailureDiagnosticTests(unittest.TestCase):
    def test_reports_only_allowlisted_failed_stage_and_exception_type(self):
        with TemporaryDirectory() as temp:
            root = Path(temp) / "runs"
            root.mkdir()
            work = root / "coden-project-synthetic"
            work.mkdir()
            (work / "events.jsonl").write_text(
                json.dumps({"role": "security", "state": "failed",
                            "error": "ValueError", "secret": "must-not-leak"}) + "\n",
                encoding="utf-8",
            )
            result = Path(temp) / "result.json"
            result.write_text(json.dumps({"directory": str(work), "status": "failed"}), encoding="utf-8")
            self.assertEqual(
                summarize(result, root),
                {"status": "failed", "stage": "security", "error_type": "ValueError"},
            )

    def test_refuses_arbitrary_paths_and_unknown_event_values(self):
        with TemporaryDirectory() as temp:
            root = Path(temp) / "runs"
            root.mkdir()
            outside = Path(temp) / "outside"
            outside.mkdir()
            (outside / "events.jsonl").write_text(
                json.dumps({"role": "security", "state": "failed", "error": "API_KEY=secret"}),
                encoding="utf-8",
            )
            result = Path(temp) / "result.json"
            result.write_text(json.dumps({"directory": str(outside), "status": "failed"}), encoding="utf-8")
            output = summarize(result, root)
            self.assertEqual(output, {"status": "diagnostic_unavailable"})
            self.assertNotIn("secret", json.dumps(output))

    def test_security_stage_reports_allowlisted_ast_reason_without_source(self):
        with TemporaryDirectory() as temp:
            root = Path(temp) / "runs"
            root.mkdir()
            work = root / "coden-project-synthetic"
            work.mkdir()
            (work / "events.jsonl").write_text(
                json.dumps({"role": "security", "state": "failed", "error": "ValueError"}) + "\\n",
                encoding="utf-8",
            )
            (work / "program.py").write_text(
                "def transform(value):\\n"
                "    return sum(1 for status in value if status in ('pending_review', 'needs_review'))\\n"
                "\\nif __name__ == '__main__':\\n    pass\\n",
                encoding="utf-8",
            )
            result = Path(temp) / "result.json"
            result.write_text(json.dumps({"directory": str(work), "status": "failed"}), encoding="utf-8")
            receipt = summarize(result, root)
            self.assertEqual(receipt["security_hint"], "unsupported_syntax")
            self.assertNotIn("pending_review", json.dumps(receipt))

    def test_missing_or_invalid_receipt_is_redacted(self):
        with TemporaryDirectory() as temp:
            self.assertEqual(
                summarize(Path(temp) / "missing.json", Path(temp)),
                {"status": "diagnostic_unavailable"},
            )

    def test_task_instructions_respect_existing_ast_policy(self):
        task = json.loads(TASK.read_text(encoding="utf-8"))
        description = task["description"].lower()
        self.assertIn("two separate if statements", description)
        self.assertNotIn("membership in", description)
        self.assertNotIn(" or status ==", description)
        inspect_source(
            "def transform(value):\n"
            "    count = 0\n"
            "    for status in value:\n"
            "        if status == 'pending_review':\n"
            "            count += 1\n"
            "        if status == 'needs_review':\n"
            "            count += 1\n"
            "    return count\n"
        )

    def test_workflow_reports_sanitized_failed_stage_without_showing_source(self):
        flow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("python -m ai_factory.factory_failure_diagnostic", flow)
        self.assertIn("exit 1", flow)


if __name__ == "__main__":
    unittest.main()
