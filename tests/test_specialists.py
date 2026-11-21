import unittest

from ai_factory.specialists import approved, parse_test


class SpecialistTests(unittest.TestCase):
    def test_literal_test_extraction(self):
        self.assertEqual(
            parse_test("assert transform([2, 3]) == 5"),
            {"input": [2, 3], "expected": 5},
        )
        for text in [
            "assert True",
            'assert transform(open("data")) == 1',
            "assert transform(1) != 1",
        ]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_test(text)

    def test_model_denial_is_binding(self):
        for value in ("BLOCK", "maybe", ""):
            with self.assertRaises(ValueError):
                approved(value)
        approved("PASS")

    def test_checkpointed_worker_exercises_package_and_holdout(self):
        import json
        import os
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from ai_factory import project
        from ai_factory.operations import Operations
        from ai_factory.specialists import work_once

        if not project.supported_host() and os.getenv("CODEN_REQUIRE_SANDBOX") != "1":
            self.skipTest("supported sandbox unavailable")
        task = json.loads((project.EXAMPLE.parent / "sum-durations.json").read_text())
        answers = [
            "edge-first",
            "summary",
            "    return sum(value)",
            "PASS",
            "7",
            "Add the supplied integers.",
            "compact",
            "PASS",
        ]
        with (
            tempfile.TemporaryDirectory() as temp,
            patch("ai_factory.local_coder.complete", side_effect=answers) as model,
        ):
            root = Path(temp)
            ops = Operations(root, task)
            try:
                for _ in range(3):
                    self.assertTrue(work_once(ops, (None, None)))
            finally:
                ops.close()
            ops = Operations(root)
            try:
                for _ in range(5):
                    self.assertTrue(work_once(ops, (None, None)))
                self.assertFalse(work_once(ops, (None, None)))
                self.assertFalse(ops.result("review")["release_authorized"])
                self.assertEqual(ops.status()["reserved_calls"], 8)
                self.assertEqual(len(ops.result("devops")["files"]), 5)
                self.assertEqual(model.call_count, 8)
            finally:
                ops.close()

    def test_denied_security_stops_dependent_stages(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from ai_factory.project import EXAMPLE
        from ai_factory.operations import Operations
        from ai_factory.specialists import work_once

        with tempfile.TemporaryDirectory() as temp:
            ops = Operations(Path(temp), json.loads(EXAMPLE.read_text()))
            self.addCleanup(ops.close)
            with (
                patch("ai_factory.specialists.sandbox_args", return_value=[]),
                patch(
                    "ai_factory.local_coder.complete",
                    side_effect=["edge-first", "analysis", "    return value", "BLOCK"],
                ),
                patch("ai_factory.specialists.lint"),
            ):
                for _ in range(3):
                    work_once(ops, (None, None))
                with self.assertRaises(ValueError):
                    work_once(ops, (None, None))
                self.assertEqual(ops.status()["tasks"]["blocked"], 4)
                self.assertFalse(work_once(ops, (None, None)))
