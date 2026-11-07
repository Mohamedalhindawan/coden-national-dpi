"""Tests for concurrency-safe transition command envelope validation."""
import unittest

from coden_enterprise.workflow import TransitionError, validate_transition_command


class TransitionCommandTests(unittest.TestCase):
    def test_accepts_well_formed_command_envelope(self):
        validate_transition_command({
            "idempotency_key": "req-2026-11-07-000001",
            "expected_version": 4,
            "requested_by": "human-reviewer-01",
        })

    def test_requires_idempotency_key(self):
        with self.assertRaises(TransitionError):
            validate_transition_command({"expected_version": 1, "requested_by": "human-01"})

    def test_rejects_short_or_oversized_idempotency_key(self):
        for key in ("short", "x" * 129):
            with self.subTest(key_length=len(key)):
                with self.assertRaises(TransitionError):
                    validate_transition_command({
                        "idempotency_key": key,
                        "expected_version": 1,
                        "requested_by": "human-01",
                    })

    def test_expected_version_must_be_positive_integer_not_boolean(self):
        for version in (0, -1, True, 1.5, "2"):
            with self.subTest(version=version):
                with self.assertRaises(TransitionError):
                    validate_transition_command({
                        "idempotency_key": "req-2026-11-07-000002",
                        "expected_version": version,
                        "requested_by": "human-01",
                    })

    def test_requester_is_required(self):
        with self.assertRaises(TransitionError):
            validate_transition_command({
                "idempotency_key": "req-2026-11-07-000003",
                "expected_version": 1,
                "requested_by": "",
            })


if __name__ == "__main__":
    unittest.main()
