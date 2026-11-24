import unittest
from ai_factory.factory_coding_wheel_review import choose_wheel, summarize


def wheel(name, size=10):
    return {"url":"https://files.pythonhosted.org/packages/"+name, "size":size,"hash":"sha256:"+"a"*64}


class CandidateWheelReviewTests(unittest.TestCase):
    def test_selects_best_compatible_not_first(self):
        a=wheel("x-1-py3-none-any.whl")
        b=wheel("x-1-cp313-cp313-manylinux_2_17_x86_64.whl")
        self.assertEqual(choose_wheel([a,b],lambda n: 0 if "cp313" in n else 1),b)

    def test_no_compatible_candidate_blocks(self):
        with self.assertRaises(ValueError):
            choose_wheel([wheel("x-1-py3-none-any.whl")],lambda n: None)

    def test_invalid_host_rejected(self):
        w=wheel("x-1-py3-none-any.whl")
        w["url"]="https://example.com/x.whl"
        with self.assertRaises(ValueError):
            choose_wheel([w],lambda n: 0)

    def test_metadata_is_not_license_approval(self):
        result=summarize([{"name":"x","status":"collected","notice_count":0,"license_expression":"MIT"}],1)
        self.assertEqual(result["without_notice"],["x"])
        self.assertFalse(result["license_approved"])
        self.assertFalse(result["runtime_compatibility_verified"])

    def test_missing_record_blocks_collection(self):
        result=summarize([],1)
        self.assertEqual(result["status"],"collection_incomplete")
