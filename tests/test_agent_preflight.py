"""Tests for the AI-agent repository preflight guardrails."""
from pathlib import Path
import tempfile
import unittest

from tools.agent_preflight import REQUIRED_FILES, REQUIRED_MARKERS, inspect_repository


class AgentPreflightTests(unittest.TestCase):
    def make_fixture(self, root: Path) -> None:
        for relative_path in REQUIRED_FILES:
            path = root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n", encoding="utf-8")
        for relative_path, markers in REQUIRED_MARKERS.items():
            path = root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("\n".join(markers), encoding="utf-8")

    def test_valid_repository_passes_all_preflight_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_fixture(root)

            results = inspect_repository(root)

            self.assertTrue(results)
            self.assertTrue(all(result["passed"] for result in results))

    def test_missing_required_file_fails_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_fixture(root)
            (root / "README.md").unlink()

            results = inspect_repository(root)

            self.assertTrue(any(
                result["name"] == "file:README.md" and not result["passed"]
                for result in results
            ))

    def test_missing_safety_marker_fails_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_fixture(root)
            (root / "AGENTS.md").write_text("missing safety guidance", encoding="utf-8")

            results = inspect_repository(root)

            self.assertTrue(any(
                result["name"].startswith("marker:AGENTS.md:")
                and not result["passed"]
                for result in results
            ))


if __name__ == "__main__":
    unittest.main()
