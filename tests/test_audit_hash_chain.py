"""Tests for append-only audit event hash-chain integrity."""
import unittest

from coden_enterprise.audit import AuditIntegrityError, append_event, verify_chain


class AuditHashChainTests(unittest.TestCase):
    def test_appends_events_with_sequence_previous_hash_and_digest(self):
        chain = []
        first = append_event(chain, {
            "event_id": "event-001", "action": "project.created",
            "actor_id": "human-001", "subject_id": "project-001",
        })
        second = append_event(chain, {
            "event_id": "event-002", "action": "task.submitted",
            "actor_id": "agent-001", "subject_id": "task-001",
        })
        self.assertEqual(first["sequence"], 1)
        self.assertEqual(second["sequence"], 2)
        self.assertEqual(second["previous_hash"], first["event_hash"])
        self.assertTrue(verify_chain(chain))

    def test_detects_payload_tampering(self):
        chain = [append_event([], {
            "event_id": "event-001", "action": "project.created",
            "actor_id": "human-001", "subject_id": "project-001",
        })]
        chain[0]["action"] = "project.deleted"
        with self.assertRaises(AuditIntegrityError):
            verify_chain(chain)

    def test_detects_event_removal_and_reordering(self):
        chain = []
        for n in range(3):
            append_event(chain, {
                "event_id": f"event-00{n+1}", "action": "task.updated",
                "actor_id": "human-001", "subject_id": f"task-00{n+1}",
            })
        with self.assertRaises(AuditIntegrityError):
            verify_chain([chain[0], chain[2]])
        with self.assertRaises(AuditIntegrityError):
            verify_chain(list(reversed(chain)))

    def test_rejects_duplicate_event_ids_and_reserved_fields(self):
        chain = [append_event([], {
            "event_id": "event-001", "action": "project.created",
            "actor_id": "human-001", "subject_id": "project-001",
        })]
        with self.assertRaises(AuditIntegrityError):
            append_event(chain, {
                "event_id": "event-001", "action": "project.updated",
                "actor_id": "human-001", "subject_id": "project-001",
            })
        with self.assertRaises(AuditIntegrityError):
            append_event(chain, {
                "event_id": "event-002", "action": "project.updated",
                "actor_id": "human-001", "subject_id": "project-001",
                "event_hash": "forged",
            })

    def test_empty_chain_is_valid(self):
        self.assertTrue(verify_chain([]))


if __name__ == "__main__":
    unittest.main()
