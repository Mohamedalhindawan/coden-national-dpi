"""Regression against the actual workflow binder, without executing the workflow."""
import ast
import hashlib
import json
import unittest
from pathlib import Path


class InventoryConsistencyTest(unittest.TestCase):
    def test_balanced_size_tampering_rejected(self):
        source = (Path(__file__).resolve().parents[1] /
                  '.github/workflows/factory-r2-native-wheel-inventory.yml').read_text()
        start = source.index('          def require(ok, message):',
                             source.index('  staging-capacity-review:'))
        end = source.index('          w=load("wheels/inventory.json")', start)
        code = '\n'.join(line[10:] for line in source[start:end].splitlines())
        namespace = {'hashlib': hashlib, 'json': json}
        exec(compile(ast.parse(code), '<workflow-binder>', 'exec'), namespace)
        records = [dict(name=f'wheel-{i}', version='1', wheel_sha256='a'*64,
                        compressed_bytes=1, expanded_member_bytes=1,
                        archive_member_count=1) for i in range(131)]
        for key, total in [('compressed_bytes',105369096),
                           ('expanded_member_bytes',301372095),
                           ('archive_member_count',14517)]:
            records[0][key] = total-130
        wheels = dict(complete=True, installed=False, records=records)
        python = dict(producer_digest_verified=True, executed=False, extracted=False,
                      sha256='45816a2653b47a6cc48d8ada4ea1185758a4c2db389d012b31e0205e5ccb548b',
                      compressed_bytes=118484282, expanded_regular_bytes=386276509,
                      archive_member_count=4525)
        capacity = dict(wheel_count=131, crc_verified=True, compressed_bytes=105369096,
                        expanded_member_bytes=301372095, archive_member_count=14517)
        # Use fixture-specific digests, retaining real hash comparisons.
        identity = sorted([r['name'],r['version'],r['wheel_sha256']] for r in records)
        keys = ('compressed_bytes','expanded_member_bytes','archive_member_count')
        bound = sorted([r['name'],r['version'],r['wheel_sha256'],*[r[k] for k in keys]] for r in records)
        digest = lambda rows: hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()
        code = code.replace('65775d2185597245ae1f2e7aa98820a4c92040bd21b4bc8e8725495dd2e6922f',digest(identity))
        code = code.replace('bebbaa4e714a76ff1a128ca98862fdb3e48cbf4775669af2e1d56b4d88f30e9a',digest(bound))
        exec(compile(ast.parse(code), '<fixture-binder>', 'exec'), namespace)
        self.assertEqual(len(namespace['bind'](wheels,python,capacity)),132)
        records[0]['expanded_member_bytes'] -= 1
        records[1]['expanded_member_bytes'] += 1
        with self.assertRaises(ValueError):
            namespace['bind'](wheels,python,capacity)
