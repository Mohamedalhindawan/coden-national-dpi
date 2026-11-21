"""Standalone acceptance tests: \`python -m unittest discover -s tests -v\`."""
import unittest
from coden_service.summary import summarize


class SummaryTests(unittest.TestCase):
    def test_empty_input(self):
        self.assertEqual(summarize([]), {
            "total": 0, "queued": 0, "in_progress": 0, "blocked": 0, "done": 0
        })

    def test_counts_synthetic_tasks(self):
        self.assertEqual(summarize([
            {"task_id": "a_01", "status": "queued", "classification": "synthetic"},
            {"task_id": "a_02", "status": "blocked", "classification": "synthetic"},
            {"task_id": "a_03", "status": "queued", "classification": "synthetic"}
        ])["queued"], 2)

    def test_denies_non_synthetic_input(self):
        with self.assertRaises(ValueError):
            summarize([{"task_id": "a_01", "status": "done", "classification": "citizen"}])

    def test_denies_extra_fields_bad_ids_and_statuses(self):
        for bad in (
            {"task_id": "../bad", "status": "queued", "classification": "synthetic"},
            {"task_id": "ok", "status": "approved", "classification": "synthetic"},
            {"task_id": "ok", "status": "queued", "classification": "synthetic", "secret": "x"},
            {"task_id": "ok", "status": None, "classification": "synthetic"}
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                summarize([bad])

    def test_denies_wrong_collection_types_and_oversized_batches(self):
        for invalid in ({"x": 1}, None, True, [{}] * 101):
            with self.subTest(invalid_type=type(invalid).__name__), self.assertRaises(ValueError):
                summarize(invalid)


    def test_rejects_duplicate_task_ids_even_with_different_statuses(self):
        with self.assertRaises(ValueError):
            summarize([
                {"task_id": "sim_1", "status": "queued", "classification": "synthetic"},
                {"task_id": "sim_1", "status": "done", "classification": "synthetic"},
            ])


if __name__ == "__main__":
    unittest.main()
