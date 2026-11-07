"""Path authorization and basic secret redaction for local CODEN sandboxing.

This is a policy helper, not an operating-system sandbox. It does not execute
code, create containers, change OS permissions, or isolate processes.
"""
import re
from pathlib import Path
from urllib.parse import urlsplit


class SandboxViolation(ValueError):
    """Raised when a requested resource exceeds the declared sandbox scope."""


_SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret)\s*([=:])\s*([^\s,;]+)"),
    re.compile(r"(?i)(password|passwd|secret)\s*([=:])\s*([^\s,;]+)"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
]


def redact_secrets(value):
    """Redact common credential-shaped strings before logs or receipts."""
    text = str(value)
    text = _SECRET_PATTERNS[0].sub(lambda m: f"{m.group(1)}{m.group(2)}[REDACTED]", text)
    text = _SECRET_PATTERNS[1].sub(lambda m: f"{m.group(1)}{m.group(2)}[REDACTED]", text)
    return _SECRET_PATTERNS[2].sub("[REDACTED]", text)


class SandboxPolicy:
    def __init__(self, workspace_root, read_scope, write_scope):
        self.root = Path(workspace_root).expanduser().resolve()
        if not self.root.exists() or not self.root.is_dir():
            raise SandboxViolation("Workspace root must be an existing directory")
        self.read_scope = tuple(read_scope or ())
        self.write_scope = tuple(write_scope or ())
        for scope in self.read_scope + self.write_scope:
            self._parse_uri(scope, allow_directory=True)

    @staticmethod
    def _parse_uri(uri, allow_directory=False):
        if not isinstance(uri, str) or not uri.startswith("workspace://"):
            raise SandboxViolation("Only workspace:// URIs are supported")
        parsed = urlsplit(uri)
        if parsed.scheme != "workspace" or not parsed.netloc or parsed.query or parsed.fragment:
            raise SandboxViolation("Malformed workspace URI")
        raw = parsed.netloc + parsed.path
        parts = [part for part in raw.split("/") if part]
        if not parts or any(part in {".", ".."} for part in parts):
            raise SandboxViolation("Traversal and empty workspace paths are forbidden")
        if any("\\" in part or "\x00" in part for part in parts):
            raise SandboxViolation("Invalid path component")
        if not allow_directory and uri.endswith("/"):
            raise SandboxViolation("A resource URI must identify a file")
        return parts

    def _scope_matches(self, uri, scopes):
        requested = self._parse_uri(uri)
        for scope in scopes:
            allowed = self._parse_uri(scope, allow_directory=True)
            if requested[:len(allowed)] == allowed:
                return True
        return False

    def authorize(self, uri, operation):
        if operation not in {"read", "write"}:
            raise SandboxViolation("Operation must be read or write")
        scopes = self.read_scope if operation == "read" else self.write_scope
        if not self._scope_matches(uri, scopes):
            raise SandboxViolation(f"{operation} is outside the declared scope")
        parts = self._parse_uri(uri)
        candidate = self.root.joinpath(*parts)
        resolved = candidate.resolve(strict=False)
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise SandboxViolation("Resolved path escapes workspace root") from exc
        # Reject symlinks in any existing path component, including the leaf.
        current = self.root
        for part in parts:
            current = current / part
            if current.is_symlink():
                raise SandboxViolation("Symlink traversal is not permitted")
        return resolved
