import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools/codex_context.py"


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(self.enterContext(tempfile.TemporaryDirectory()))
        subprocess.run(["git", "init", "-q", self.repo], check=True)

    def put(self, path, data):
        target = self.repo / path
        target.parent.mkdir(exist_ok=True, parents=True)
        target.write_bytes(data)
        subprocess.run(["git", "add", "--", path], cwd=self.repo, check=True)

    def query(self, value, *args):
        return subprocess.run([sys.executable, SCRIPT, value, "--json", *args],
                              capture_output=True, text=True, cwd=self.repo)

    def test_rank_unicode_scope_and_limit(self):
        self.put("a.md", "راجع البناء هنا".encode())
        self.put("b.py", "class مثال:\n    async def البناء(self):\n        return 'طلب'\n".encode())
        result = self.query("البناء", "--limit", "1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [
            {"path": "b.py", "line": 2, "symbol": "البناء", "match": "البناء"}])
        self.assertEqual(json.loads(self.query("طلب").stdout)[0]["symbol"], "البناء")
        self.assertEqual(self.query("البناء").stdout, self.query("البناء").stdout)
        self.assertNotEqual(self.query("البناء", "--limit", "0").returncode, 0)

    def test_skip_secret_paths_untracked_binary_and_links(self):
        for p in ("secret.yaml", "private/credentials.json", ".env.local.md", "bin.md"):
            self.put(p, b'needle' if p != 'bin.md' else b'needle\x00')
        (self.repo / "untracked.md").write_text("needle")
        (self.repo / "link.md").symlink_to(self.repo / "untracked.md")
        subprocess.run(["git", "add", "link.md"], cwd=self.repo, check=True)
        self.put("old/visible.md", b"old")
        os.rename(self.repo / "old", self.repo / "moved")
        (self.repo / "moved/visible.md").write_text("needle")
        (self.repo / "old").symlink_to(self.repo / "moved", target_is_directory=True)
        self.assertEqual(json.loads(self.query("needle").stdout), [])

    def test_handles_invalid_python_and_does_not_copy_line_contents(self):
        self.put("bad.py", b"if (broken:  # needle sensitive example")
        result = json.loads(self.query("needle").stdout)
        self.assertEqual(result[0]["line"], 1)
        self.assertNotIn("sensitive", str(result))
