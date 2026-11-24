import unittest
import json
from email.parser import BytesParser
from ai_factory.factory_coding_wheel_review import choose_wheel, summarize, metadata_fields, primary_metadata


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

    def test_non_ascii_header_serializes_without_losing_evidence(self):
        m = BytesParser().parsebytes(b"License: Caf\xc3\xa9\nLicense-Expression: MIT\nLicense-File: LICENSE\n\n")
        fields = metadata_fields(m)
        self.assertEqual(json.loads(json.dumps(fields))["license"], str(m["License"]))
        self.assertEqual(fields["license_expression"], "MIT")

    def test_large_incompatible_wheel_does_not_block_small_compatible(self):
        a = wheel("x-1-py3-none-any.whl")
        b = wheel("x-1-cp312-cp312-win_amd64.whl", 100*1024*1024)
        self.assertEqual(choose_wheel([b,a],lambda n: None if "win" in n else 0),a)

    def test_root_distribution_metadata_not_vendored_metadata(self):
        outer={"base64":"outer"}
        nested={"base64":"nested"}
        self.assertEqual(primary_metadata({"setuptools-84.2.1.dist-info/METADATA":outer,
            "setuptools/_vendor/x-1.dist-info/METADATA":nested}),outer)

    def test_two_root_metadata_records_block(self):
        with self.assertRaises(ValueError):
            primary_metadata({"a-1.dist-info/METADATA":{}, "b-1.dist-info/METADATA":{}})
