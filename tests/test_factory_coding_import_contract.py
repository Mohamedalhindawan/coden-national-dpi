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
