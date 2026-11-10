import copy
import unittest
from enterprise.performance.kpi_preflight import preflight_kpi_record, preflight_kpi_registry

BASE = {"kpi_id": "kpi-1", "objective_id": "obj-1", "name": "Synthetic", "unit": "count", "baseline": 1, "target": 2, "direction": "increase", "measurement_frequency": "monthly", "status": "draft", "created_at": "2026-11-10T00:00:00Z"}

class KpiIntegrityTests(unittest.TestCase):
    def test_nonfinite_values_rejected(self):
        for value in (float('nan'), float('inf'), float('-inf')):
            with self.subTest(value=str(value)):
                self.assertIn('invalid_numeric_baseline', preflight_kpi_record(dict(BASE, baseline=value)))
                self.assertIn('invalid_numeric_target', preflight_kpi_record(dict(BASE, target=value)))

    def test_duplicate_identifiers_rejected(self):
        self.assertIn('kpis[1]:duplicate_kpi_id', preflight_kpi_registry({'kpis': [BASE, copy.deepcopy(BASE)]}))

    def test_unhashable_identifier_fails_closed(self):
        self.assertIn('kpis[0]:invalid_kpi_id', preflight_kpi_registry({'kpis': [dict(BASE, kpi_id=[])]}))

    def test_valid_unique_records(self):
        self.assertEqual([], preflight_kpi_registry({'kpis': [BASE, dict(BASE, kpi_id='kpi-2')]}))

    def test_read_only(self):
        source = {'kpis': [dict(BASE, baseline=float('inf'))]}
        before = copy.deepcopy(source)
        preflight_kpi_registry(source)
        self.assertEqual(source, before)

if __name__ == '__main__':
    unittest.main()
