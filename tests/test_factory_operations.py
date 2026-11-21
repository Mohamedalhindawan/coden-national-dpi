import json
from pathlib import Path
import tempfile
import unittest

from ai_factory.operations import Operations
from ai_factory.project import EXAMPLE


class OperationsTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.task = json.loads(EXAMPLE.read_text())
        self.ops = Operations(self.root, self.task)
        self.addCleanup(self.ops.close)

    def test_pause_restart_and_resume(self):
        self.ops.pause(True)
        later = Operations(self.root)
        self.addCleanup(later.close)
        self.assertIsNone(later.claim())
        later.pause(False)
        claim = later.claim()
        self.assertEqual(claim["task_id"], "orchestrator")
        later.complete(claim, {"plan": "bounded"})
        self.assertEqual(self.ops.claim()["task_id"], "architecture")

    def test_reservation_is_single_and_durable(self):
        claim = self.ops.claim()
        receipt = self.ops.reserve(claim, 400)
        self.assertEqual(receipt["estimated_cost_usd"], 0)
        with self.assertRaises(ValueError):
            self.ops.reserve(claim, 400)
        self.assertEqual(self.ops.status()["reserved_calls"], 1)
        self.ops.fail(claim, "synthetic rejection")
        self.assertEqual(self.ops.status()["tasks"]["blocked"], 7)

    def test_conflicting_submission_is_rejected(self):
        with self.assertRaises(ValueError):
            Operations(self.root, dict(self.task, description="different"))
