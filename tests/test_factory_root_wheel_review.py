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


DEFAULT_HEADERS = "Metadata-Version: 2.4\nRequires-Python: >=3.12\nLicense-Expression: MIT\nLicense-File: LICENSE\n"
DEFAULT_WHEEL = b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
DEFAULT_ENTRYPOINT = b"[console_scripts]\nagent-server = openhands.agent_server.__main__:main\n"


def candidate(name, version="1.63.1", notice=NOTICE, extra=None, headers="", payload_path=None,
              base_headers=DEFAULT_HEADERS, wheel_headers=DEFAULT_WHEEL, entrypoint="default"):
    prefix = name.replace("-", "_") + "-" + version + ".dist-info/"
    files = {prefix + "METADATA": f"Name: {name}\nVersion: {version}\n{base_headers}{headers}".encode(),
             prefix + "WHEEL": wheel_headers,
             (payload_path or "openhands/" + name.removeprefix("openhands-").replace("-", "_") + "/fixture.py"): b"# synthetic only\n"}
    if entrypoint == "default":
        entrypoint = DEFAULT_ENTRYPOINT if name == "openhands-agent-server" else None
    if entrypoint is not None:
        files[prefix + "entry_points.txt"] = entrypoint
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


    def test_pinned_lock_metadata_contract(self):
        # Small independent lock fixture, never treated as real R2 admission.
        lock = ("\n".join(
            '[[package]]\nname = "' + name + '"\nversion = "1.63.1"\n'
            '[package.metadata]\nrequires-dist = [{name="demo",specifier=">=1,<2"}, '
            '{name="addon",marker="extra == \'feature\'"}]\nprovides-extras=["feature"]'
            for name in ROOTS) + "\n").encode()
        good = 'Requires-Dist: Demo<2, >=1\nRequires-Dist: addon; extra == "feature"\nProvides-Extra: feature\n'
        rows = [candidate(n, headers=good) for n in ROOTS]
        with patch.object(audit, "ROOT_METADATA_LOCK_SHA256", hashlib.sha256(lock).hexdigest(), create=True):
            result = audit.inspect_root_wheel_outputs(rows, lock_bytes=lock)
            self.assertTrue(result["metadata_dependencies_verified"])
            self.assertEqual(result["metadata_requirement_count"], 8)
            self.assertFalse(result["installation_authorized"])
            for headers in (good.replace(">=1", ">=0"), good.replace("addon; extra", "addon; python_version"),
                            good + "Requires-Dist: browser-use\n",
                            good + "Requires-Dist: demo>=1,<2\n",
                            good.replace("Provides-Extra: feature\n", ""),
                            good.replace("Demo<2, >=1", "demo @ https://example.invalid/a.whl")):
                with self.subTest(headers=headers), self.assertRaises(ValueError):
                    audit.inspect_root_wheel_outputs(rows[:3]+[candidate(ROOTS[-1], headers=headers)], lock_bytes=lock)
            with self.assertRaises(ValueError):
                audit.inspect_root_wheel_outputs(rows, lock_bytes=lock+b"\n")


    def test_root_install_paths_do_not_overlap(self):
        result = audit.inspect_root_wheel_outputs(self.rows)
        self.assertTrue(result["root_install_paths_disjoint"])
        self.assertFalse(result["external_install_paths_verified"])
        self.assertFalse(result["installation_authorized"])

    def test_reject_cross_root_file_and_ancestor_collisions(self):
        for path in ("openhands/sdk/fixture.py", "openhands/sdk",
                     "openhands/sdk/fixture.py/nested.py",
                     "OpenHands/sdk/other.py",
                     "openhands_agent_server-1.63.1.data/purelib/openhands/sdk/fixture.py",
                     "outside_root.py"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                audit.inspect_root_wheel_outputs(
                    self.rows[:3]+[candidate(ROOTS[-1], payload_path=path)])


    def test_root_generated_metadata_review(self):
        result = audit.inspect_root_wheel_outputs(self.rows)
        self.assertTrue(result["root_generated_metadata_verified"])
        self.assertEqual(result["console_script_count"], 1)
        self.assertFalse(result["installation_authorized"])

    def test_reject_wrong_generated_metadata_or_entrypoints(self):
        invalid = [
            dict(base_headers=DEFAULT_HEADERS.replace(">=3.12", ">=3.14")),
            dict(base_headers=DEFAULT_HEADERS.replace("MIT", "GPL-3.0-only")),
            dict(base_headers=DEFAULT_HEADERS + "License-File: OTHER\n"),
            dict(base_headers=DEFAULT_HEADERS + "Requires-Python: >=3.12\n"),
            dict(wheel_headers=DEFAULT_WHEEL.replace(b"true", b"false")),
            dict(wheel_headers=DEFAULT_WHEEL.replace(b"py3-none-any", b"cp313-cp313-linux_x86_64")),
            dict(wheel_headers=DEFAULT_WHEEL+b"Tag: py3-none-any\n"),
            dict(entrypoint=None),
            dict(entrypoint=DEFAULT_ENTRYPOINT.replace(b"__main__:main",b"other:main")),
            dict(entrypoint=DEFAULT_ENTRYPOINT+b"\n[other]\nx = something:run\n"),
            dict(entrypoint=DEFAULT_ENTRYPOINT+b"agent-server = openhands.agent_server.__main__:main\n"),
        ]
        for options in invalid:
            with self.subTest(options=options), self.assertRaises(ValueError):
                audit.inspect_root_wheel_outputs(self.rows[:3]+[candidate(ROOTS[-1], **options)])
        with self.assertRaises(ValueError):
            audit.inspect_root_wheel_outputs([candidate(ROOTS[0], entrypoint=DEFAULT_ENTRYPOINT)]+self.rows[1:])
