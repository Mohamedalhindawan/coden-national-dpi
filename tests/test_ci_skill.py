import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

HELPER = Path(__file__).resolve().parents[1] / ".agents/skills/gh-fix-ci/scripts/inspect_pr_checks.py"
spec = importlib.util.spec_from_file_location("ci_skill", HELPER)
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)


class SkillTests(unittest.TestCase):
    def test_classify_checks(self):
        self.assertFalse(ci.is_failing({"state": "SUCCESS"}))
        self.assertTrue(ci.is_failing({"bucket": "fail"}))

    def test_failing_and_unavailable_log(self):
        check = {"name": "contract", "link": "https://github.com/demo/repo/actions/runs/123/job/2"}
        with patch.object(ci, "run_gh_command") as gh:
            gh.side_effect = [ci.GhResult(0, "{}", ""), ci.GhResult(0, "setup\nERROR bad contract", "")]
            self.assertIn("ERROR bad contract", ci.analyze_check(check, Path("."), 3, 1)["logSnippet"])
            gh.side_effect = [ci.GhResult(0, "{}", ""), ci.GhResult(1, "", "expired")]
            self.assertEqual(ci.analyze_check(check, Path("."), 3, 1)["status"], "log_unavailable")

    def test_old_gh_fallback_checks_status_context_and_check_run(self):
        with patch.object(ci, "run_gh_command") as gh:
            gh.side_effect = [ci.GhResult(1, "", "unknown flag: --json"),
                              ci.GhResult(0, '{"statusCheckRollup":[{"context":"legacy","state":"ERROR","targetUrl":"https://example.invalid"},{"name":"contract","conclusion":"FAILURE"}]}', "")]
            checks = ci.fetch_checks("124", Path("."))
            self.assertTrue(all(ci.is_failing(check) for check in checks))
            self.assertEqual(checks[0]["name"], "legacy")
            self.assertEqual(checks[0]["detailsUrl"], "https://example.invalid")

    def test_nonzero_with_valid_check_results_is_diagnostic_input(self):
        with patch.object(ci, "run_gh_command", return_value=ci.GhResult(1, '[{"state":"FAILURE"}]', "")):
            self.assertEqual(ci.fetch_checks("1", Path(".")), [{"state":"FAILURE"}])

    def test_external_check_does_not_trigger_a_github_request(self):
        with patch.object(ci, "run_gh_command", side_effect=AssertionError):
            result = ci.analyze_check({"link": "https://example.invalid/runs/123"}, Path("."), 3, 1)
            self.assertEqual(result["status"], "external")

    def test_diagnosis_uses_the_failing_job_in_a_multi_job_run(self):
        check = {"link": "https://github.com/demo/demo/actions/runs/123/job/456"}
        with patch.object(ci, "run_gh_command") as gh:
            gh.side_effect = [ci.GhResult(0, "{}", ""), ci.GhResult(0, "ERROR contract", "")]
            ci.analyze_check(check, Path("."), 3, 1)
            self.assertEqual(gh.call_args.args[0], ["run","view","123","--job","456","--log"])

    def test_small_window_keeps_failure_marker(self):
        text = "prepare\nERROR invalid contract\ncleanup\ncleanup\ncleanup"
        self.assertIn("ERROR", ci.extract_failure_snippet(text, max_lines=1, context=20))
