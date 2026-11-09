"""Fail-closed V4 progress measurement: fixtures do not represent accepted work."""
import json
import math
import unittest
from pathlib import Path

MANIFEST = Path(__file__).resolve().parents[1] / 'enterprise/governance/v4-measurement-baseline.json'
DOMAINS = {'governance_documentation', 'ai_engineering_factory', 'tamam_dpi', 'security_testing_operations'}

def completion_rates(data):
    if not isinstance(data, dict) or data.get('source_verified') is not True:
        return None
    phases = data.get('phases')
    if not isinstance(phases, list) or len(phases) != 8:
        return None
    if [p.get('id') for p in phases if isinstance(p, dict)] != [f'V4-P{i}' for i in range(1, 9)]:
        return None
    if set(data.get('domains', [])) != DOMAINS or len(data.get('domains', [])) != 4:
        return None
    total = 0.0
    done = 0.0
    seen_requirement_ids = set()
    for p in phases:
        if p.get('verified') is not True or not isinstance(p.get('title'), str) or not p['title'].strip():
            return None
        weight = p.get('weight')
        requirements = p.get('requirements')
        if type(weight) not in (int, float) or not math.isfinite(weight) or weight <= 0:
            return None
        if not isinstance(requirements, list) or not requirements:
            return None
        total += weight
        for r in requirements:
            if not isinstance(r, dict) or type(r.get('completed')) is not bool or r.get('domain') not in DOMAINS:
                return None
            rid = r.get('id')
            if not isinstance(rid, str) or not rid.strip() or rid != rid.strip() or rid.casefold() in seen_requirement_ids:
                return None
            seen_requirement_ids.add(rid.casefold())
            if r['completed']:
                if any(not isinstance(r.get(k), str) or not r[k].strip() for k in ('reviewed_evidence', 'executed_tests', 'acceptance_reference')):
                    return None
                if r.get('human_accepted') is not True:
                    return None
        done += weight * sum(r['completed'] for r in requirements) / len(requirements)
    pct = round(100 * done / total, 2)
    return pct, round(100 - pct, 2)

class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(MANIFEST.read_text(encoding='utf-8'))

    def fixture(self):
        d = self.data
        d['source_verified'] = True
        for i, p in enumerate(d['phases']):
            p.update(title=f'Fixture phase {i+1}', weight=1, verified=True, requirements=[{'id':f'FIXTURE-REQ-{i+1}', 'completed': i < 4, 'domain':'governance_documentation', 'reviewed_evidence':'commit:fixture', 'executed_tests':'run:fixture', 'acceptance_reference':'approval:fixture', 'human_accepted':True}])
        return d

    def test_unverified_baseline_unmeasurable(self):
        self.assertIsNone(completion_rates(self.data))
        self.assertEqual(len(self.data['phases']), 8)

    def test_verified_fixture_complements_to_100(self):
        self.assertEqual(completion_rates(self.fixture()), (50.0, 50.0))

    def test_missing_evidence_blocks_measurement(self):
        d=self.fixture(); del d['phases'][0]['requirements'][0]['executed_tests']
        self.assertIsNone(completion_rates(d))

    def test_unverified_title_blocks_measurement(self):
        d=self.fixture(); d['phases'][0]['title']=None
        self.assertIsNone(completion_rates(d))

    def test_boolean_weight_rejected(self):
        d=self.fixture(); d['phases'][0]['weight']=True
        self.assertIsNone(completion_rates(d))

    def test_nan_weight_rejected(self):
        d=self.fixture(); d['phases'][0]['weight']=float('nan')
        self.assertIsNone(completion_rates(d))

    def test_string_completed_rejected(self):
        d=self.fixture(); d['phases'][0]['requirements'][0]['completed']='false'
        self.assertIsNone(completion_rates(d))

    def test_missing_domain_rejected(self):
        d=self.fixture(); del d['phases'][0]['requirements'][0]['domain']
        self.assertIsNone(completion_rates(d))

    def test_missing_acceptance_reference_rejected(self):
        d=self.fixture(); del d['phases'][0]['requirements'][0]['acceptance_reference']
        self.assertIsNone(completion_rates(d))

    def test_duplicate_phase_rejected(self):
        d=self.fixture(); d['phases'][1]['id']='V4-P1'
        self.assertIsNone(completion_rates(d))

    def test_missing_requirement_id_rejected(self):
        d=self.fixture(); del d['phases'][0]['requirements'][0]['id']
        self.assertIsNone(completion_rates(d))

    def test_duplicate_requirement_id_rejected(self):
        d=self.fixture(); d['phases'][1]['requirements'][0]['id']=d['phases'][0]['requirements'][0]['id']
        self.assertIsNone(completion_rates(d))

    def test_blank_requirement_id_rejected(self):
        d=self.fixture(); d['phases'][0]['requirements'][0]['id']='  '
        self.assertIsNone(completion_rates(d))

    def test_case_variant_requirement_id_rejected(self):
        d=self.fixture(); d['phases'][1]['requirements'][0]['id']=d['phases'][0]['requirements'][0]['id'].lower()
        self.assertIsNone(completion_rates(d))

    def test_whitespace_padded_requirement_id_rejected(self):
        d=self.fixture(); d['phases'][0]['requirements'][0]['id']=' '+d['phases'][0]['requirements'][0]['id']
        self.assertIsNone(completion_rates(d))

    def test_missing_human_acceptance_rejected(self):
        d=self.fixture(); d['phases'][0]['requirements'][0]['human_accepted']=False
        self.assertIsNone(completion_rates(d))

if __name__ == '__main__':
    unittest.main()
