import base64
import csv
import hashlib
import io
import unittest
import zipfile
from unittest.mock import patch
from ai_factory import factory_wheel_notice_audit as audit


ROOTS = ("openhands-sdk", "openhands-tools", "openhands-workspace", "openhands-agent-server")
NOTICE = b"trusted synthetic notice"


def candidate(name, version="1.63.1", notice=NOTICE, extra=None):
    prefix = name.replace("-", "_") + "-" + version + ".dist-info/"
    files = {prefix + "METADATA": f"Name: {name}\nVersion: {version}\n".encode(),
             prefix + "WHEEL": b"Wheel-Version: 1.0\nTag: py3-none-any\n",
             "openhands/fixture.py": b"# synthetic only\n"}
    if notice is not None:
        files[prefix + "licenses/LICENSE"] = notice
    if extra is not None:
        files[extra] = b"\x7fELFfixture"
    rows = [[p, "sha256=" + base64.urlsafe_b64encode(hashlib.sha256(b).digest()).decode().rstrip("="), str(len(b))]
            for p, b in files.items()]
    rows.append([prefix + "RECORD", "", ""])
    record = io.StringIO(newline="")
    csv.writer(record, lineterminator="\n").writerows(rows)
    files[prefix + "RECORD"] = record.getvalue().encode()
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p, b in files.items():
            z.writestr(p, b)
    raw = out.getvalue()
    return raw, hashlib.sha256(raw).hexdigest()


class RootWheelReviewTest(unittest.TestCase):
    def setUp(self):
        # Only test data substitutes a license pin; production pin is immutable.
        self.pin = patch.object(audit, "ROOT_NOTICE_SHA256", hashlib.sha256(NOTICE).hexdigest(), create=True)
        self.pin.start()
        self.addCleanup(self.pin.stop)
        self.rows = [candidate(n) for n in ROOTS]

    def test_exact_four_roots_with_full_record_and_notice(self):
        result = audit.inspect_root_wheel_outputs(self.rows)
        self.assertEqual(result["root_count"], 4)
        self.assertTrue(result["record_verified"])
        self.assertTrue(result["source_notice_match"])
        for key in ("source_to_wheel_verified", "metadata_dependencies_verified", "installation_authorized", "release_authorized"):
            self.assertIs(result[key], False)

    def test_reject_missing_or_duplicate_roots(self):
        for rows in (self.rows[:3], self.rows[:3]+self.rows[:1], self.rows[:3]+[candidate("different")]):
            with self.subTest(count=len(rows)), self.assertRaises(ValueError):
                audit.inspect_root_wheel_outputs(rows)

    def test_reject_wrong_version_or_missing_or_wrong_notice(self):
        for item in (candidate(ROOTS[-1], version="1.63.2"), candidate(ROOTS[-1], notice=None), candidate(ROOTS[-1], notice=b"wrong")):
            with self.assertRaises(ValueError):
                audit.inspect_root_wheel_outputs(self.rows[:3]+[item])

    def test_reject_elf_member_and_digest_mismatch(self):
        raw, _ = self.rows[-1]
        for item in (candidate(ROOTS[-1], extra="openhands/fixture.so"), (raw, "0"*64)):
            with self.assertRaises(ValueError):
                audit.inspect_root_wheel_outputs(self.rows[:3]+[item])
