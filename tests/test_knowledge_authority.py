"""Synthetic-only, read-only source-of-truth selection for CODEN RAG metadata."""
import copy
import unittest
from ai_factory import knowledge_authority

REV = "c" * 40
HASH = "a" * 64


def registry(**extra):
    return dict({
        "schema": "coden.knowledge.authority.v1",
        "doc_id": "adr_015",
        "source_system": "github",
        "source_revision": REV,
        "source_sha256": HASH,
        "classification": "synthetic",
        "approved": True,
        "deleted": False,
        "authorized_principals": ["reviewer_01"],
    }, **extra)


def record(**extra):
    return dict({
        "doc_id": "adr_015",
        "source_system": "github",
        "source_revision": REV,
        "source_sha256": HASH,
    }, **extra)


class AuthorityGateTests(unittest.TestCase):
    def test_approved_canonical_source_selected_without_content(self):
        docs = [record(source_system="notion", source_revision="summary_v1"),
                record()]
        result = knowledge_authority.resolve_candidate(registry(), docs, "reviewer_01")
        self.assertEqual(result["decision"], "candidate")
        self.assertEqual(result["source_system"], "github")
        self.assertEqual(result["source_revision"], REV)
        self.assertFalse(result["retrieval_authorized"])
        self.assertFalse(result["source_content_verified"])
        self.assertNotIn("content", result)

    def test_denied_principal_gets_no_identifying_document_metadata(self):
        out = knowledge_authority.resolve_candidate(registry(), [record()], "other_01")
        self.assertEqual(out, {"decision": "deny", "retrieval_authorized": False})

    def test_stale_notion_summary_cannot_replace_canonical_github(self):
        out = knowledge_authority.resolve_candidate(
            registry(), [record(source_system="notion", source_revision="summary_v8")], "reviewer_01")
        self.assertEqual(out["decision"], "blocked")
        self.assertFalse(out["retrieval_authorized"])

    def test_changed_revision_or_hash_is_blocked(self):
        for changed in ({"source_revision": "d"*40}, {"source_sha256": "f"*64}):
            with self.subTest(changed=changed):
                out = knowledge_authority.resolve_candidate(registry(), [record(**changed)], "reviewer_01")
                self.assertEqual(out["decision"], "blocked")

    def test_revoked_deleted_unapproved_are_denied(self):
        for changed in ({"deleted": True}, {"approved": False}):
            with self.subTest(changed=changed):
                out=knowledge_authority.resolve_candidate(registry(**changed), [record()], "reviewer_01")
                self.assertEqual(out["decision"], "deny")

    def test_duplicate_canonical_candidates_are_blocked(self):
        out=knowledge_authority.resolve_candidate(registry(), [record(),record()], "reviewer_01")
        self.assertEqual(out["decision"], "blocked")

    def test_malformed_metadata_and_excessive_candidates_rejected(self):
        for changed in ({"authorized_principals": ["reviewer_01", "reviewer_01"]},
                        {"classification":"citizen"}, {"source_sha256": "short"},
                        {"approved": "yes"}, {"secret": "must_not_be_here"}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                knowledge_authority.resolve_candidate(registry(**changed), [record()], "reviewer_01")
        with self.assertRaises(ValueError):
            knowledge_authority.resolve_candidate(registry(), [record()]*33, "reviewer_01")

    def test_source_record_unknown_fields_and_nonstring_principal_rejected(self):
        with self.assertRaises(ValueError):
            knowledge_authority.resolve_candidate(registry(), [record(content="private_text")], "reviewer_01")
        with self.assertRaises(ValueError):
            knowledge_authority.resolve_candidate(registry(), [record()], ["reviewer_01"])

    def test_conflicting_authority_evidence_never_falls_back_to_summary(self):
        docs=[record(source_sha256="d"*64),
              record(source_system="notion", source_revision="latest_summary")]
        out=knowledge_authority.resolve_candidate(registry(), docs, "reviewer_01")
        self.assertEqual(out["decision"], "blocked")
        self.assertNotIn("source_system", out)


if __name__ == "__main__":
    unittest.main()
