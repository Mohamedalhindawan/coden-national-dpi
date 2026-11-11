"""Offline PR snapshot drift detector. No network, no merge authority."""
import unittest

REQUIRED = {26, *range(37, 55)}


def detect_drift(snapshot, live):
    """Return deterministic differences; missing live records are unknown, not unchanged."""
    old = {p['number']: p for p in snapshot}
    new = {p['number']: p for p in live}
    if len(old) != len(snapshot) or len(new) != len(live):
        raise ValueError('duplicate PR number')
    if set(old) != REQUIRED:
        raise ValueError('incomplete baseline')
    changes = []
    for number in sorted(REQUIRED):
        if number not in new:
            changes.append((number, 'unverified', None, None))
            continue
        for key in ('state', 'merged', 'base_ref', 'head_ref', 'head_sha'):
            if key not in old[number] or key not in new[number]:
                changes.append((number, 'missing_' + key, old[number].get(key), new[number].get(key)))
            elif old[number][key] != new[number][key]:
                changes.append((number, key, old[number][key], new[number][key]))
    return changes


class DriftTests(unittest.TestCase):
    def setUp(self):
        self.base = [dict(number=n, state='open', merged=False, base_ref='main', head_ref=f'b{n}', head_sha='a'*40) for n in sorted(REQUIRED)]

    def test_no_drift(self):
        self.assertEqual(detect_drift(self.base, self.base), [])

    def test_missing_live_record_is_unverified(self):
        self.assertEqual(detect_drift(self.base, self.base[1:]), [(26, 'unverified', None, None)])

    def test_changed_sha_and_state_are_reported(self):
        live = [dict(p) for p in self.base]
        live[0]['head_sha'] = 'b'*40
        live[0]['state'] = 'closed'
        self.assertEqual([x[1] for x in detect_drift(self.base, live)], ['state', 'head_sha'])

    def test_duplicate_live_number_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            detect_drift(self.base, self.base + [self.base[0]])

    def test_incomplete_baseline_rejected(self):
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            detect_drift(self.base[:-1], self.base)

    def test_missing_field_not_silently_equal(self):
        live = [dict(p) for p in self.base]
        del live[0]['merged']
        self.assertEqual(detect_drift(self.base, live)[0][1], 'missing_merged')


if __name__ == '__main__':
    unittest.main()
