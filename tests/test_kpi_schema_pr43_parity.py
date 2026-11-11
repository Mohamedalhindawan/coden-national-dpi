"""Pinned cross-branch contract checks against PR #43 schema blob 827d5a4d.

These checks do not declare a canonical schema or approve KPI registry migration.
"""
import unittest
from enterprise.performance import kpi_preflight as validator

# Snapshot of relevant fields in PR #43 schemas/enterprise/kpi.schema.json.
REQUIRED = {'kpi_id', 'objective_id', 'name', 'unit', 'baseline', 'target', 'direction', 'measurement_frequency', 'status', 'created_at'}
OPTIONAL = {'definition', 'owner_id'}

class KpiSchemaParityTest(unittest.TestCase):
    def test_required_and_allowed_fields_match_pr43(self):
        self.assertEqual(set(validator.REQUIRED_CANONICAL), REQUIRED)
        self.assertEqual(set(validator.ALLOWED_FIELDS), REQUIRED | OPTIONAL)

    def test_enum_sets_match_pr43(self):
        self.assertEqual(set(validator.DIRECTIONS), {'increase', 'decrease', 'maintain'})
        self.assertEqual(set(validator.FREQUENCIES), {'daily', 'weekly', 'monthly', 'quarterly', 'annually', 'ad_hoc'})
        self.assertEqual(set(validator.STATUSES), {'draft', 'active', 'paused', 'retired'})

    def test_unknown_schema_property_is_rejected(self):
        record = {'kpi_id':'kpi-001','objective_id':'obj-001','name':'Synthetic KPI','unit':'count','baseline':0,'target':1,'direction':'increase','measurement_frequency':'monthly','status':'draft','created_at':'2026-11-11T00:00:00Z','not_in_schema':42}
        self.assertEqual(validator.preflight_kpi_record(record), ['unknown_canonical_field:not_in_schema'])

if __name__ == '__main__':
    unittest.main()
