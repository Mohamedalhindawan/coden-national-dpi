import unittest

from skills.orchestration.worker_runtime import WorkerAdmissionController, WorkerRuntimeError


class WorkerAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.controller = WorkerAdmissionController(
            max_workers=2,
            allowed_worker_ids=["worker-a", "worker-b", "worker-c"],
            allowed_task_kinds=["synthetic-test", "documentation-check"],
        )

    def test_admits_only_configured_workers_and_task_kinds(self):
        self.controller.register_worker("worker-a", ["synthetic-test"])
        self.controller.register_worker("worker-b", ["documentation-check"])
        self.assertTrue(self.controller.can_accept("worker-a", "synthetic-test"))
        self.assertFalse(self.controller.can_accept("worker-a", "documentation-check"))

    def test_rejects_unknown_worker_and_capability(self):
        with self.assertRaises(WorkerRuntimeError):
            self.controller.register_worker("intruder", ["synthetic-test"])
        with self.assertRaises(WorkerRuntimeError):
            self.controller.register_worker("worker-a", ["unlisted-capability"])

    def test_enforces_global_and_per_worker_concurrency(self):
        self.controller.register_worker("worker-a", ["synthetic-test"], max_concurrency=2)
        self.controller.register_worker("worker-b", ["synthetic-test"], max_concurrency=2)
        self.controller.acquire_slot("worker-a", "job-1", "synthetic-test")
        self.controller.acquire_slot("worker-a", "job-2", "synthetic-test")
        with self.assertRaises(WorkerRuntimeError):
            self.controller.acquire_slot("worker-a", "job-3", "synthetic-test")
        with self.assertRaises(WorkerRuntimeError):
            self.controller.acquire_slot("worker-b", "job-4", "synthetic-test")

    def test_releases_only_slots_owned_by_same_worker(self):
        self.controller.register_worker("worker-a", ["synthetic-test"])
        self.controller.acquire_slot("worker-a", "job-1", "synthetic-test")
        with self.assertRaises(WorkerRuntimeError):
            self.controller.release_slot("worker-b", "job-1")
        self.controller.release_slot("worker-a", "job-1")
        self.assertEqual(self.controller.active_count, 0)

    def test_rejects_duplicate_job_ids_and_unknown_release(self):
        self.controller.register_worker("worker-a", ["synthetic-test"])
        self.controller.acquire_slot("worker-a", "job-1", "synthetic-test")
        with self.assertRaises(WorkerRuntimeError):
            self.controller.acquire_slot("worker-a", "job-1", "synthetic-test")
        with self.assertRaises(WorkerRuntimeError):
            self.controller.release_slot("worker-a", "missing")

    def test_pause_blocks_new_admissions_but_keeps_existing_slots(self):
        self.controller.register_worker("worker-a", ["synthetic-test"])
        self.controller.acquire_slot("worker-a", "job-1", "synthetic-test")
        self.controller.pause()
        self.assertEqual(self.controller.active_count, 1)
        with self.assertRaises(WorkerRuntimeError):
            self.controller.acquire_slot("worker-a", "job-2", "synthetic-test")
        self.controller.resume()
        self.controller.acquire_slot("worker-a", "job-2", "synthetic-test")
