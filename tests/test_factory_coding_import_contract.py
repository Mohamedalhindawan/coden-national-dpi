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
