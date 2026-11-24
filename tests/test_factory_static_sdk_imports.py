import unittest
from ai_factory.factory_static_sdk_imports import inspect_imports, compare_imports


class StaticSdkImportTests(unittest.TestCase):
    def test_missing_module_and_symbol(self):
        refs = inspect_imports({"parent.py": "from browser_use_sdk.v2 import Client\nimport browser_use_sdk.old"})
        result = compare_imports(refs, {"browser_use_sdk/v2.py": "class NewClient: pass"})
        self.assertEqual(result["missing_modules"], ["browser_use_sdk.old"])
        self.assertEqual(result["unverified_symbols"], ["browser_use_sdk.v2:Client"])
        self.assertFalse(result["runtime_compatibility_verified"])

    def test_export_and_submodule(self):
        refs = inspect_imports({"parent.py": "from browser_use_sdk import Client, models"})
        result = compare_imports(refs, {"browser_use_sdk/__init__.py": "from .client import Client", "browser_use_sdk/models.py": "", "browser_use_sdk/client.py": "class Client: pass"})
        self.assertEqual(result["missing_modules"], [])
        self.assertEqual(result["unverified_symbols"], [])
        self.assertFalse(result["runtime_compatibility_verified"])

    def test_non_sdk_imports_ignored(self):
        self.assertEqual(inspect_imports({"parent.py": "import os\nfrom other import browser_use_sdk"}), [])
