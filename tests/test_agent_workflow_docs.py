"""Contract checks for the free-first AI agent workflow documents; no secrets or services."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "docs" / "AGENT_WORKFLOW.md"
PR_TEMPLATE = ROOT / ".github" / "pull_request_template.md"
README = ROOT / "README.md"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "prototype-checks.yml"

SECRET_PATTERNS = (
    r"sk-[A-Za-z0-9]{16,}",
    r"ghp_[A-Za-z0-9]{20,}",
    r"AKIA[0-9A-Z]{16}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"(?i)bearer\s+[A-Za-z0-9\-._~+/]{20,}",
)

MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


class AgentWorkflowDocsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.pr_template = PR_TEMPLATE.read_text(encoding="utf-8")
        cls.readme = README.read_text(encoding="utf-8")
        cls.ci = CI_WORKFLOW.read_text(encoding="utf-8")

    def test_workflow_includes_existing_tooling_audit(self):
        self.assertIn("Audit of existing repository tooling", self.workflow)
        self.assertIn("AGENTS.md", self.workflow)
        self.assertIn("Prototype checks", self.workflow)
        self.assertIn("No dependency files", self.workflow)

    def test_workflow_defines_the_six_logical_roles(self):
        for role in (
            "Coordinator",
            "Frontend",
            "Backend / API",
            "Testing",
            "Security reviewer",
            "Documentation",
        ):
            with self.subTest(role=role):
                self.assertIn(role, self.workflow)

    def test_workflow_separates_verified_capabilities_from_unverified_options(self):
        self.assertIn("Confirmed in this environment", self.workflow)
        self.assertIn("Not verified here", self.workflow)
        self.assertIn("GitHub API", self.workflow)
        self.assertIn("cannot create pull requests automatically", self.workflow)
        self.assertIn("no paid subscription", self.workflow)

    def test_workflow_requires_human_approval_and_synthetic_data(self):
        self.assertIn("Human approval gates", self.workflow)
        self.assertIn("Do not merge without a human review", self.workflow)
        self.assertIn("Synthetic data only", self.workflow)
        self.assertIn("Do not modify repository settings", self.workflow)
        self.assertIn("identity, payments, eligibility, security", self.workflow)

    def test_workflow_is_usable_from_an_android_phone(self):
        self.assertIn("Android", self.workflow)
        self.assertIn("Freebuff", self.workflow)
        self.assertIn("GitHub mobile", self.workflow)
        self.assertIn("Run workflow", self.workflow)
        self.assertIn("Compare & pull request", self.workflow)

    def test_workflow_provides_a_copyable_task_template(self):
        self.assertIn("Task template", self.workflow)
        self.assertIn("Copy this into a GitHub issue", self.workflow)
        self.assertIn("Acceptance criteria", self.workflow)
        self.assertIn("Out of scope", self.workflow)
        self.assertIn("Security and privacy notes", self.workflow)

    def test_pr_template_covers_gates_and_evidence(self):
        for heading in (
            "## Scope and data",
            "## Tests actually run",
            "## Security and privacy",
            "## Human approval",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, self.pr_template)
        self.assertIn("Synthetic or demo data only", self.pr_template)
        self.assertIn("No secrets", self.pr_template)
        self.assertIn("merge", self.pr_template.lower())

    def test_documentation_links_resolve_to_repository_files(self):
        for source in (README, WORKFLOW):
            text = source.read_text(encoding="utf-8")
            for target in MARKDOWN_LINK.findall(text):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                path = target.split("#", 1)[0]
                if not path:
                    continue
                with self.subTest(source=source.name, target=target):
                    self.assertTrue((source.parent / path).resolve().exists())

    def test_workflow_documents_contain_no_secret_like_strings(self):
        for name, text in (("workflow", self.workflow), ("pr_template", self.pr_template)):
            for pattern in SECRET_PATTERNS:
                with self.subTest(document=name, pattern=pattern):
                    self.assertIsNone(re.search(pattern, text))

    def test_ci_workflow_still_runs_tests_and_openapi_validation(self):
        self.assertIn("python -m unittest discover -s tests -v", self.ci)
        self.assertIn("openapi-spec-validator==0.7.2", self.ci)
        self.assertIn("workflow_dispatch:", self.ci)
        self.assertIn("contents: read", self.ci)

    def test_readme_links_the_operational_workflow(self):
        self.assertIn("[Free-first AI agent workflow](docs/AGENT_WORKFLOW.md)", self.readme)


if __name__ == "__main__":
    unittest.main()
