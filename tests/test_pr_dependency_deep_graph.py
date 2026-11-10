"""Deep dependency graph regression: validation must not exhaust Python recursion."""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "pr_dependency_validator",
    Path(__file__).resolve().parents[1] / "enterprise/governance/pr_dependency_validator.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def inventory(count, cycle=False):
    return {
        "merge_policy": "human_review_only",
        "items": [
            {
                "pr": n,
                "url": f"https://github.com/Mohamedalhindawan/coden-national-dpi/pull/{n}",
                "review": "required",
                "decision": "pending",
                "ci": "not_verified_in_this_snapshot",
                "depends_on": ([n - 1] if n > 1 else ([count] if cycle else [])),
            }
            for n in range(1, count + 1)
        ],
    }


class DeepGraphTests(unittest.TestCase):
    def test_long_acyclic_chain(self):
        self.assertEqual(module.validate_inventory(inventory(1200)), [])

    def test_long_chain_with_cycle(self):
        self.assertTrue(any("cycle" in error for error in module.validate_inventory(inventory(1200, cycle=True))))


if __name__ == "__main__":
    unittest.main()
