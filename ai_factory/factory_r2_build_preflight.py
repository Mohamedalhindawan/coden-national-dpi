"""Read-only composite R2 preflight; observations never grant build admission."""
import argparse
import hashlib
import json
import os
import stat
import tarfile

from .factory_build_materials import review_build_materials, _open_directory, _review_file, _stamp
from .factory_root_inventory import reproduce_inventory

R2_ARCHIVE = 'CODEN_R2_Patched_Source_REVIEW_ONLY.tar.gz'
SOURCE_PINS = {
    'CODEN_R2_Original_Source_077f3fad_REVIEW_ONLY.tar.gz': (6697588, '40b5f4b2017644f34ffc5044d6c670ad6bd57ac84cd897a178cc9944ca25f6eb'),
    R2_ARCHIVE: (6697662, 'e44613f882ec5e306723e156417966e2c63f3d06d019897d722bcd4a068a03d6'),
    'CODEN_R2_Source_With_Proposed_Notice_REVIEW_ONLY.tar.gz': (6700845, 'ccd7c4b9a71b404cdc870cda61b72f437dbd65ff452edbf09cce43ab2b91b69d'),
}


def _inventory_from_source(fd):
    size, digest = SOURCE_PINS[R2_ARCHIVE]
    with os.fdopen(os.open(R2_ARCHIVE, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                           dir_fd=fd), 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size != size:
            raise ValueError('unsafe source archive')
        raw = stream.read(size + 1)
        if (len(raw) != size or hashlib.sha256(raw).hexdigest() != digest
                or _stamp(before) != _stamp(os.fstat(stream.fileno()))
                or _stamp(before) != _stamp(os.stat(R2_ARCHIVE, dir_fd=fd, follow_symlinks=False))):
            raise ValueError('source archive mismatch')
    return reproduce_inventory(raw)


def review_preflight(materials_directory, source_directory):
    """Combine byte observations of exact stage inputs and retained source.

    The material directory must be dedicated; unrelated source-directory
    entries are ignored. Nothing is extracted or executed. An exact match
    does not establish a common immutable snapshot, approval, or build
    success. The proposed notice amendment is not adopted by this function.
    """
    materials = review_build_materials(materials_directory)
    fd = _open_directory(source_directory)
    try:
        sources = {name: _review_file(fd, name, size, digest)
                   for name, (size, digest) in sorted(SOURCE_PINS.items())}
        inventory_sha = None
        if sources[R2_ARCHIVE] == 'MATCH':
            try:
                inventory_sha = hashlib.sha256(_inventory_from_source(fd)).hexdigest()
            except (OSError, ValueError, tarfile.TarError, EOFError):
                pass
    finally:
        os.close(fd)
    source_match = all(status == 'MATCH' for status in sources.values())
    complete = materials['pinned_materials_match'] and source_match and inventory_sha is not None
    return {'status': 'R2_INPUT_BYTES_REVIEW_ONLY' if complete else 'R2_INPUTS_BLOCKED',
            'input_bytes_complete': complete, 'materials': materials,
            'source_archives': sources, 'source_archive_pins_match': source_match,
            'source_inventory_reproduced': inventory_sha is not None,
            'source_inventory_sha256': inventory_sha,
            'missing_build_materials': [name for name, state in materials['materials'].items() if state == 'MISSING'],
            'independent_review': False, 'immutable_mount_verified': False,
            'amendment_adopted': False, 'actual_build_performed': False,
            'source_to_wheel_verified': False, 'build_authorized': False,
            'installation_authorized': False, 'release_authorized': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('materials_directory')
    parser.add_argument('source_directory')
    args = parser.parse_args(argv)
    try:
        result = review_preflight(args.materials_directory, args.source_directory)
    except (OSError, ValueError):
        result = {'status': 'R2_INPUTS_BLOCKED', 'input_bytes_complete': False,
                  'build_authorized': False, 'installation_authorized': False,
                  'release_authorized': False}
    print(json.dumps(result, sort_keys=True))
    return 0 if result['input_bytes_complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
