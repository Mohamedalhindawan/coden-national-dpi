"""Offline review of exact R2 build-only staged input bytes, never execution."""
import argparse
import hashlib
import json
import os
import stat

# Exact retained build and offline installation manifests. Notice amendment
# is a separate proposal, NOT an adopted patch or a permission decision.
PINS = {
    "cpython-3.13.15+20260814-x86_64-unknown-linux-gnu-install_only.tar.gz": (118484282, "45816a2653b47a6cc48d8ada4ea1185758a4c2db389d012b31e0205e5ccb548b"),
    "setuptools-84.2.1-py3-none-any.whl": (876263, "ca140b45d5325a9478f880e351484f62fef15f336462e449ca0c03c873d589c2"),
    "wheel-0.46.3-py3-none-any.whl": (30557, "4b399d56c9d9338230118d705d9737a2a468ccca63d5e813e2a4fc7815d8bc4d"),
    "packaging-26.3-py3-none-any.whl": (129956, "d7193f7c8e4e93f444fde0262bf90af30e16fa0ad0ad44cb553c87339b23cd1c"),
    "pyo3-candidate.lock": (248633, "93447ba7c43d7c8bffe1bb66d99abad1eaffcbd0d11fe1ef5bb776c7155998a3"),
    "coding-profile-source.patch": (6522, "0609700a143b3fc8b0439f7ff2c74b75aa41c220fa9ba4294db35bac54b8f70f"),
    "CODEN_R2_Notice_Amendment_PROPOSED.patch": (6469, "9cc84596a0c04e261aaf30b0b59c3a5ae3c2e26854ac158fbdee512cddb7a655"),
    "root-wheel-build-manifest-UNAPPROVED.json": (12515, "f396d96fe5e8f3cf1f38c2c786f749929f4bc3cc40cd9470a590c43facb9d19b"),
    "r2-offline-installation-manifest-UNAPPROVED.json": (100812, "b307d4bd91c3e2e9705aaf23872345b4910740deacdc08150ca8e7041a0c4819"),
}


def _open_directory(path):
    path = os.fspath(path)
    if not isinstance(path, str) or not path or ".." in path.split("/"):
        raise ValueError("invalid staging directory")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open("/" if path.startswith("/") else ".", flags)
    try:
        for part in path.split("/"):
            if part in ("", "."):
                continue
            child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def _stamp(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _review_file(directory, name, size, digest):
    try:
        with os.fdopen(os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                               dir_fd=directory), "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                return "UNSAFE_FILE"
            if before.st_size != size:
                return "SIZE_MISMATCH"
            hasher = hashlib.sha256()
            remaining = size
            while remaining:
                block = stream.read(min(remaining, 1024 * 1024))
                if not block:
                    return "SIZE_MISMATCH"
                hasher.update(block)
                remaining -= len(block)
            if stream.read(1) or _stamp(before) != _stamp(os.fstat(stream.fileno())):
                return "CHANGED_DURING_READ"
            if _stamp(before) != _stamp(os.stat(name, dir_fd=directory, follow_symlinks=False)):
                return "CHANGED_DURING_READ"
            return "MATCH" if hasher.hexdigest() == digest else "DIGEST_MISMATCH"
    except FileNotFoundError:
        return "MISSING"
    except OSError:
        return "UNSAFE_OR_UNREADABLE"


def review_build_materials(directory):
    """Read exact inputs only. This is not an authenticated immutable mount.

    Use a dedicated trusted staging directory. No extraction, network, source
    checkout, dependency installation, or authorization follows from a match.
    Results are observations, not an admission token or protection against
    modifications after review. Reject unexpected entries without reading them.
    """
    fd = _open_directory(directory)
    try:
        unexpected = 0
        with os.scandir(fd) as entries:
            for entry in entries:
                if entry.name not in PINS:
                    unexpected += 1
                    if unexpected >= 32:
                        break
        rows = {name: _review_file(fd, name, size, digest)
                for name, (size, digest) in sorted(PINS.items())}
    finally:
        os.close(fd)
    matched = sum(status == "MATCH" for status in rows.values())
    complete = matched == len(PINS) and unexpected == 0
    return {"status": "BUILD_INPUT_BYTES_REVIEW_ONLY" if complete else "BUILD_INPUTS_BLOCKED",
            "pinned_materials_match": complete, "matched": matched,
            "expected": len(PINS), "unexpected_entries": unexpected,
            "unexpected_count_capped": unexpected == 32, "materials": rows,
            "source_tree_verified": False, "immutable_mount_verified": False,
            "independent_review": False, "amendment_adopted": False,
            "build_authorized": False, "installation_authorized": False,
            "release_authorized": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory")
    args = parser.parse_args(argv)
    try:
        result = review_build_materials(args.directory)
    except (OSError, ValueError):
        result = {"status": "BUILD_INPUTS_BLOCKED", "pinned_materials_match": False,
                  "build_authorized": False, "installation_authorized": False,
                  "release_authorized": False}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["pinned_materials_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
