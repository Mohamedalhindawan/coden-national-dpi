import unittest
from ai_factory.factory_coding_import_contract import check_absence, BANNED


class CodingImportContractTests(unittest.TestCase):
    def test_installed_distribution_blocks_even_without_importable_module(self):
        errors=check_absence(["Browser_Use-SDK"], lambda name: None)
        self.assertIn("distribution:browser-use-sdk",errors)

    def test_discoverable_module_blocks_even_without_distribution(self):
        errors=check_absence([], lambda name: object() if name=="lmnr" else None)
        self.assertIn("module:lmnr",errors)

    def test_discovery_failure_is_not_absence(self):
        def lookup(name):
            raise ImportError("broken discovery")
        self.assertEqual(len(check_absence([],lookup)),len(BANNED))

    def test_clean_inventory(self):
        self.assertEqual(check_absence(["openhands-sdk"],lambda name: None),[])

    def test_legacy_entrypoint_cannot_import_before_independent_admission(self):
        import contextlib
        import io
        import json
        from unittest.mock import patch
        from ai_factory import factory_coding_import_contract as contract

        # No SDK import is performed by this test, even on the old code.
        stream = io.StringIO()
        with patch.object(contract, "current_absence", return_value=[]) as discovery:
            with patch("importlib.import_module") as importer:
                with contextlib.redirect_stdout(stream):
                    rc = contract.main()
        self.assertNotEqual(rc, 0)
        discovery.assert_not_called()
        importer.assert_not_called()
        result = json.loads(stream.getvalue())
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("independent_r2_admission_required", result["errors"])
        self.assertEqual(result["imported"], [])
        self.assertFalse(result["runtime_admitted"])
        self.assertFalse(result["sdk_conversation_ran"])
        self.assertFalse(result["release_authorized"])


class R2BundlePreflightTests(unittest.TestCase):
    def test_bundle_checks_actual_four_metadata_inputs_and_keeps_import_blocked(self):
        import hashlib
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from ai_factory import modeb_import_probe as probe
        digest = lambda b: hashlib.sha256(b).hexdigest()
        lock = b"fixture lock"
        manifest = b"fixture manifest"
        roots = b"fixture build manifest"
        closure = json.dumps(dict(lock_sha256=digest(lock), wheel_manifest_sha256=digest(manifest),
            workspace_roots=probe.ROOTS, runtime_external_records=126,
            dependency_records=[dict(name="fixture-"+str(i)) for i in range(126)],
            **{key:False for key in ("adopted","security_approved","legal_approved",
              "installation_authorized","import_authorized","release_authorized")})).encode()
        with tempfile.TemporaryDirectory() as tmp, patch.multiple(probe,
                EXPECTED_LOCK_SHA=digest(lock), EXPECTED_MANIFEST_SHA=digest(manifest),
                EXPECTED_CONTRACT_SHA=digest(closure), EXPECTED_ROOT_BUILD_SHA=digest(roots)):
            paths = {}
            for key, raw in (("closure", closure), ("lock", lock), ("manifest", manifest),
                             ("root_build", roots)):
                paths[key] = Path(tmp)/key
                paths[key].write_bytes(raw)
            result = probe.validate_r2_bundle(**paths)
            self.assertEqual(result["status"], "STATIC_R2_BUNDLE_MATCH_UNAPPROVED")
            self.assertEqual(result["verified_metadata_files"], 4)
            self.assertFalse(result["sdk_imported"])
            self.assertFalse(result["installation_authorized"])
            self.assertFalse(result["import_authorized"])
            self.assertFalse(result["release_authorized"])
            for key in ("lock", "manifest", "root_build", "closure"):
                original = paths[key].read_bytes()
                paths[key].write_bytes(original+b" ")
                with self.subTest(key=key), self.assertRaises(ValueError):
                    probe.validate_r2_bundle(**paths)
                paths[key].write_bytes(original)
            with self.assertRaisesRegex(ValueError, "independent_r2_admission_required"):
                probe.inspect(paths["closure"], digest(closure))

    def test_bundle_rejects_nonregular_and_oversized_metadata_without_reading(self):
        import os
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from ai_factory import modeb_import_probe as probe
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            regular = root/"file"
            regular.write_bytes(b"x")
            alias = root/"alias"
            alias.symlink_to(regular)
            big = root/"big"
            big.write_bytes(b"x"*(probe.MAX_BUNDLE_METADATA+1))
            with patch.object(probe, "validate_r2_contract", return_value={}):
                for path in (alias, big, root):
                    with self.subTest(path=path), self.assertRaises((ValueError, OSError)):
                        probe.validate_r2_bundle(closure=regular, lock=path,
                                                manifest=regular, root_build=regular)

    def test_cli_blocked_receipt_explicitly_denies_installation(self):
        import contextlib
        import io
        import json
        from ai_factory import modeb_import_probe as probe
        for args in (
            ["--closure", "unused", "--operator-approved-import-only"],
            ["--closure", "unused", "--validate-contract-only", "--lock", "unused"],
        ):
            with self.subTest(args=args), contextlib.redirect_stdout(io.StringIO()) as stream:
                self.assertEqual(probe.main(args), 1)
                receipt = json.loads(stream.getvalue())
                for key in ("sdk_imported", "installation_authorized",
                            "import_authorized", "release_authorized"):
                    self.assertIs(receipt[key], False)

    def test_contract_only_receipt_explicitly_denies_installation(self):
        import hashlib
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from ai_factory import modeb_import_probe as probe
        raw = json.dumps(dict(lock_sha256=probe.EXPECTED_LOCK_SHA,
            wheel_manifest_sha256=probe.EXPECTED_MANIFEST_SHA,
            workspace_roots=probe.ROOTS, runtime_external_records=126,
            dependency_records=[dict(name="fixture-"+str(i)) for i in range(126)],
            **{key:False for key in ("adopted","security_approved","legal_approved",
               "installation_authorized","import_authorized","release_authorized")})).encode()
        with tempfile.TemporaryDirectory() as tmp, patch.object(
                probe, "EXPECTED_CONTRACT_SHA", hashlib.sha256(raw).hexdigest()):
            closure = Path(tmp)/"closure"
            closure.write_bytes(raw)
            receipt = probe.validate_r2_contract(closure)
            self.assertIs(receipt["installation_authorized"], False)
