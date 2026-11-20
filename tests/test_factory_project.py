import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_factory import project


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.task = json.loads(project.EXAMPLE.read_text())

    def run_project(self, source=None):
        return project.run(self.task, self.root, source)

    def events(self, run):
        return [
            json.loads(line) for line in (run / "events.jsonl").read_text().splitlines()
        ]

    def test_policy_blocks_before_reading_code(self):
        for change in [
            {"estimated_cost_usd": 1},
            {"requested_actions": ["deploy"]},
            {"data_classification": "private"},
            {"review_cases": []},
        ]:
            with self.subTest(change=change):
                task = dict(self.task, **change)
                run, status = project.run(task, self.root, self.root / "absent.py")
                self.assertEqual(status, "blocked")
                self.assertEqual(len(self.events(run)), 1)
                self.assertFalse((run / "candidate.pyz").exists())

    def test_security_rejects_unsupported_code(self):
        path = self.root / "candidate.py"
        path.write_text("import sys\ndef transform(value):\n    return value\n")
        run, status = self.run_project(path)
        self.assertEqual(status, "failed")
        self.assertEqual(self.events(run)[-1]["role"], "security")
        self.assertFalse((run / "candidate.pyz").exists())

    def test_dependency_failure_stops_pipeline(self):
        with patch.object(project, "lint", side_effect=RuntimeError("disabled")):
            run, status = self.run_project()
        self.assertEqual(status, "failed")
        self.assertFalse((run / "candidate.pyz").exists())

    def test_lint_detects_undefined_variable(self):
        with self.assertRaises(ValueError):
            project.lint("def transform(value):\n    return missing\n")

    def test_eight_roles_packaging_and_independent_review(self):
        self.require_sandbox()
        run, status = self.run_project()
        self.assertEqual(status, "awaiting_human_review")
        self.assertEqual(
            set(e["role"] for e in self.events(run)),
            set(
                "orchestrator architecture coding security testing documentation devops review".split()
            ),
        )
        receipt = json.loads((run / "review.json").read_text())
        self.assertEqual(receipt["sha256"], project.digest(run / "candidate.pyz"))
        self.assertFalse(receipt["release_authorized"])
        self.assertEqual(
            project.execute(run / "candidate.pyz", ["z", "z", "a"]), {"a": 1, "z": 2}
        )
        second, _ = self.run_project()
        self.assertEqual(project.digest(second / "candidate.pyz"), receipt["sha256"])

    def test_review_rejects_code_passing_only_visible_cases(self):
        self.require_sandbox()
        self.task["review_cases"] = [{"input": ["a"], "expected": {"bad": 0}}]
        run, status = self.run_project()
        self.assertEqual(status, "failed")
        self.assertEqual(self.events(run)[-1]["role"], "review")
        self.assertFalse((run / "review.json").exists())

    def test_second_project_from_local_source(self):
        self.require_sandbox()
        self.task.update(
            recipe="python-transform",
            cases=[{"input": [1, 2], "expected": 3}],
            review_cases=[{"input": [], "expected": 0}],
        )
        src = self.root / "sum.py"
        src.write_text("def transform(value):\n    return sum(value)\n")
        run, status = self.run_project(src)
        self.assertEqual(status, "awaiting_human_review")
        self.assertEqual(project.execute(run / "candidate.pyz", [4, 5]), 9)

    def require_sandbox(self):
        import os

        if not project.supported_host() and os.getenv("CODEN_REQUIRE_SANDBOX") != "1":
            self.skipTest("needs supported Linux bubblewrap runtime")

    def test_private_review_input_is_not_an_acceptance_example(self):
        self.task["review_cases"] = self.task["cases"][:1]
        self.assertEqual(self.run_project()[1], "blocked")

    def test_bad_local_model_digest_fails_without_template_fallback(self):
        from ai_factory import local_coder

        bad = self.root / "wrong"
        bad.write_bytes(b"not the approved archive")
        with self.assertRaises(ValueError):
            local_coder.check_file(bad, local_coder.CPU_SHA)
        with patch.object(project, "sandbox_args", return_value=[]):
            run, status = project.run(self.task, self.root, local_assets=(bad, bad))
        self.assertEqual(status, "failed")
        self.assertEqual(self.events(run)[-1]["role"], "coding")
        self.assertFalse((run / "program.py").exists())

    def test_offline_prompt_withholds_review_examples(self):
        import tarfile
        from types import SimpleNamespace

        from ai_factory import local_coder

        archive = self.root / "fake.tar"
        with tarfile.open(archive, "w"):
            pass
        model = self.root / "fake.gguf"
        model.write_bytes(b"demo")
        with (
            patch.object(local_coder, "check_file"),
            patch.object(local_coder.subprocess, "run") as generate,
        ):
            generate.return_value = SimpleNamespace(
                returncode=0, stdout=b"    return value\n```"
            )
            source = local_coder.generate(
                archive,
                model,
                "echo",
                [{"input": "visible", "expected": "visible"}],
                ["sandbox"],
            )
        self.assertIn("return value", source)
        cmd = generate.call_args.args[0]
        self.assertIn("--offline", cmd)
        self.assertIn("transform('visible')", cmd[-1])

    def test_sandbox_controlled_fixture(self):
        self.require_sandbox()
        script = self.root / "probe.py"
        script.write_text(
            "import json, os\nfrom pathlib import Path\n"
            "print(json.dumps([os.environ.get('CODEN_PROBE'), Path('/workspace').exists(), "
            "os.statvfs('/').f_flag & os.ST_RDONLY != 0]))"
        )
        with patch.dict("os.environ", {"CODEN_PROBE": "synthetic"}):
            self.assertEqual(project.execute(script, None), [None, False, True])
