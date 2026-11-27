import hashlib
import json
import unittest
from unittest.mock import patch
from ai_factory import factory_root_source_payload as review


class RootSourcePayloadTests(unittest.TestCase):
    def setUp(self):
        self.roots = ("openhands-sdk", "openhands-tools", "openhands-workspace", "openhands-agent-server")
        self.paths = {n: "openhands/" + n.removeprefix("openhands-").replace("-", "_") + "/fixture.py" for n in self.roots}
        self.digest = hashlib.sha256(b"fixture").hexdigest()
        self.expected = {"roots": {n: {p: {"sha256": self.digest, "bytes": 7, "required": True}} for n, p in self.paths.items()}}
        self.raw = json.dumps(self.expected).encode()
        self.override = patch.object(review, "EXPECTED_SHA256", hashlib.sha256(self.raw).hexdigest())
        self.override.start()
        self.addCleanup(self.override.stop)
        self.receipt = {"record_verified": True, "root_install_paths_disjoint": True, "metadata_dependencies_verified": True, "release_authorized": False,
                        "wheels": [{"distribution": {"name": n, "version": "1.63.1"}, "files": {p: {"sha256": self.digest, "bytes": 7, "record_hash_verified": True}}} for n,p in self.paths.items()]}

    def test_exact_source_members_are_review_only(self):
        result = review.compare_root_source_payloads(self.receipt, self.raw)
        self.assertEqual(result["matched_payload_files"], 4)
        self.assertTrue(result["source_payload_match"])
        for key in ("receipt_origin_verified", "source_to_wheel_verified", "build_authorized", "installation_authorized", "release_authorized"):
            self.assertIs(result[key], False)

    def test_reject_changed_missing_or_unknown_member(self):
        for mutation in ("changed", "missing", "unexpected", "unverified", "wrong_size"):
            with self.subTest(mutation=mutation):
                receipt = json.loads(json.dumps(self.receipt))
                files = receipt["wheels"][0]["files"]
                path = self.paths[self.roots[0]]
                if mutation == "changed": files[path]["sha256"] = "0"*64
                elif mutation == "missing": del files[path]
                elif mutation == "unexpected": files[path+".extra"] = files[path]
                elif mutation == "unverified": files[path]["record_hash_verified"] = False
                else: files[path]["bytes"] = 8
                with self.assertRaises(ValueError): review.compare_root_source_payloads(receipt,self.raw)

    def test_reject_missing_gate_duplicate_root_or_tampered_manifest(self):
        for field in ("record_verified", "root_install_paths_disjoint", "metadata_dependencies_verified"):
            receipt = dict(self.receipt, **{field:False})
            with self.assertRaises(ValueError): review.compare_root_source_payloads(receipt,self.raw)
        with self.assertRaises(ValueError): review.compare_root_source_payloads(dict(self.receipt,wheels=self.receipt["wheels"][:3]+self.receipt["wheels"][:1]),self.raw)
        with self.assertRaises(ValueError): review.compare_root_source_payloads(self.receipt,self.raw+b"\n")
