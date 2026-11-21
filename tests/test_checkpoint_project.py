"""Checkpoint adapter boundary tests for the existing offline project runner."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_factory import checkpoint, checkpoint_project, project


class CheckpointProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = self.root / "checkpoints"
        self.task = json.loads(project.EXAMPLE.read_text())
        self.branch = "feat/factory-adopt-first"
        self.commit = "a" * 40

    def launch(self):
        return checkpoint_project.run_with_checkpoint(self.task, self.root, self.store,
                                                      branch=self.branch, commit=self.commit)

    def test_valid_review_result_writes_review_gate_without_approval(self):
        with patch.object(project, "run", return_value=(self.root / "work", "awaiting_human_review")) as runner:
            result = self.launch()
        self.assertEqual(result["status"], "awaiting_human_review")
        self.assertEqual(result["journal"]["status"], "awaiting_human_review")
        self.assertFalse(result["journal"]["execution_authorized"])
        self.assertEqual(result["journal"]["event_count"], 3)
        runner.assert_called_once()

    def test_blocked_result_is_preserved_as_blocked(self):
        with patch.object(project, "run", return_value=(self.root / "work", "blocked")):
            result = self.launch()
        self.assertEqual(result["journal"]["status"], "blocked")
        self.assertEqual(result["journal"]["next_action"], "inspect_offline_logs")

    def test_unhandled_worker_exception_records_pause(self):
        with patch.object(project, "run", side_effect=OSError("private details")):
            with self.assertRaises(OSError):
                self.launch()
        state = checkpoint.read(self.store, self.task["id"])
        self.assertEqual(state["status"], "paused")
        self.assertEqual(state["pause_reason"], "worker_failed")
        self.assertNotIn("private", (self.store / (self.task["id"] + ".jsonl")).read_text())

    def test_invalid_task_makes_no_journal_or_run(self):
        self.task["data_classification"] = "private"
        with patch.object(project, "run") as runner, self.assertRaises(ValueError):
            self.launch()
        runner.assert_not_called()
        self.assertFalse(self.store.exists())

    def test_existing_journal_prevents_reexecution(self):
        with patch.object(project, "run", return_value=(self.root / "work", "blocked")) as runner:
            self.launch()
            with self.assertRaises(FileExistsError):
                self.launch()
        self.assertEqual(runner.call_count, 1)

    def test_actual_project_pipeline_if_sandbox_available(self):
        if not project.supported_host() and os.getenv("CODEN_REQUIRE_SANDBOX") != "1":
            self.skipTest("requires supported Linux sandbox")
        result = self.launch()
        self.assertEqual(result["status"], "awaiting_human_review")
        self.assertTrue((result["directory"] / "review.json").is_file())
        self.assertEqual(checkpoint.read(self.store, self.task["id"])["status"], "awaiting_human_review")


if __name__ == "__main__":
    unittest.main()
