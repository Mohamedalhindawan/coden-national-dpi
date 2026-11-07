import unittest

from skills.orchestration.dag import (
    DAGError, build_execution_plan, ready_tasks, propagate_blocked, retry_allowed
)


class TaskDAGTests(unittest.TestCase):
    def graph(self):
        return [
            {"task_id": "design", "depends_on": []},
            {"task_id": "api", "depends_on": ["design"]},
            {"task_id": "ui", "depends_on": ["design"]},
            {"task_id": "integration", "depends_on": ["api", "ui"]},
        ]

    def test_builds_deterministic_parallel_waves(self):
        plan = build_execution_plan(self.graph())
        self.assertEqual(plan["waves"], [
            ["design"], ["api", "ui"], ["integration"]
        ])
        self.assertEqual(plan["task_count"], 4)

    def test_rejects_duplicate_unknown_self_and_cyclic_dependencies(self):
        with self.assertRaises(DAGError):
            build_execution_plan([{"task_id": "a", "depends_on": []},
                                  {"task_id": "a", "depends_on": []}])
        with self.assertRaises(DAGError):
            build_execution_plan([{"task_id": "a", "depends_on": ["missing"]}])
        with self.assertRaises(DAGError):
            build_execution_plan([{"task_id": "a", "depends_on": ["a"]}])
        with self.assertRaises(DAGError):
            build_execution_plan([{"task_id": "a", "depends_on": ["b"]},
                                  {"task_id": "b", "depends_on": ["a"]}])

    def test_ready_tasks_require_all_dependencies_succeeded(self):
        states = {"design": "succeeded", "api": "pending", "ui": "pending",
                  "integration": "pending"}
        self.assertEqual(ready_tasks(self.graph(), states), ["api", "ui"])
        states["api"] = "succeeded"
        states["ui"] = "succeeded"
        self.assertEqual(ready_tasks(self.graph(), states), ["integration"])

    def test_failed_dependency_blocks_all_transitive_descendants(self):
        blocked = propagate_blocked(self.graph(), {"design": "failed"})
        self.assertEqual(blocked, ["api", "integration", "ui"])

    def test_retry_is_bounded_by_task_policy(self):
        self.assertTrue(retry_allowed({"max_retries": 2}, attempts=1))
        self.assertFalse(retry_allowed({"max_retries": 2}, attempts=2))
        self.assertFalse(retry_allowed({"max_retries": 0}, attempts=0))
        with self.assertRaises(DAGError):
            retry_allowed({"max_retries": 99}, attempts=0)

    def test_rejects_invalid_states_and_duplicate_dependencies(self):
        with self.assertRaises(DAGError):
            ready_tasks(self.graph(), {"design": "mystery"})
        with self.assertRaises(DAGError):
            build_execution_plan([{"task_id": "a", "depends_on": ["b", "b"]},
                                  {"task_id": "b", "depends_on": []}])


if __name__ == "__main__":
    unittest.main()
