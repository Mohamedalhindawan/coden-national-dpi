"""PR #53 template compatibility guard, with no migration or real KPI values."""
from pathlib import Path
import unittest

from enterprise.performance.kpi_preflight import preflight_kpi_registry

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'enterprise/performance/kpi-registry.yaml'


def template_fields(text):
    """Read only the literal top-level required_fields sequence; fail on drift."""
    lines = text.splitlines()
    assert lines.count('required_fields:') == 1, 'ambiguous required_fields section'
    start = lines.index('required_fields:') + 1
    result = []
    for line in lines[start:]:
        if line.startswith('  - '):
            result.append(line[4:].strip())
        elif not line.strip() or line.lstrip().startswith('#'):
            continue
        else:
            break
    return result


class LegacyKpiTemplateContract(unittest.TestCase):
    def test_legacy_template_remains_explicitly_unapproved(self):
        text = TEMPLATE.read_text(encoding='utf-8')
        self.assertIn('kpis: []', text)
        self.assertEqual(preflight_kpi_registry({'kpis': []}), ['empty_template_not_approved'])

    def test_legacy_fields_require_human_mapping(self):
        fields = template_fields(TEMPLATE.read_text(encoding='utf-8'))
        self.assertIn('id', fields)
        self.assertNotIn('kpi_id', fields)
        self.assertNotIn('objective_id', fields)
        legacy = {key: 'synthetic' for key in fields}
        errors = preflight_kpi_registry({'kpis': [legacy]})
        self.assertIn('kpis[0]:human_mapping_required_id_to_kpi_id', errors)
        self.assertIn('kpis[0]:missing_canonical_kpi_id', errors)
        self.assertIn('kpis[0]:missing_canonical_objective_id', errors)

    def test_legacy_template_fields_do_not_silently_become_canonical(self):
        fields = template_fields(TEMPLATE.read_text(encoding='utf-8'))
        self.assertEqual(len(fields), len(set(fields)))
        self.assertEqual(set(fields) - {'name', 'definition', 'measurement_frequency', 'baseline', 'target'},
                         {'id', 'formula', 'data_source', 'accountable_owner', 'observed_value', 'evidence_url', 'reviewed_at'})


if __name__ == '__main__':
    unittest.main()
