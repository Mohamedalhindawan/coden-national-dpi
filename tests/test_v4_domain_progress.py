import unittest
from enterprise.governance.v4_domain_progress import calculate_domain_progress

class DomainProgressTests(unittest.TestCase):
    def fixture(self):
        domains = ['governance_documentation', 'ai_engineering_factory', 'tamam_dpi', 'security_testing_operations']
        return {'source_verified': True, 'domains': domains, 'phases': [dict(id=f'V4-P{i+1}', verified=True, title=f'Phase {i+1}', weight=2 if i==0 else 1, requirements=[dict(id=f'R{i+1}', domain=domains[i%4], completed=i==0, human_accepted=True, reviewed_evidence='evidence', executed_tests='run', acceptance_reference='approval')]) for i in range(8)]}
    def test_weighted_rates(self):
        r=calculate_domain_progress(self.fixture())
        self.assertEqual(r['overall'], (22.22, 77.78))
        self.assertEqual(r['domains']['governance_documentation'], (66.67, 33.33))
        self.assertEqual(r['domains']['tamam_dpi'], (0.0, 100.0))
    def test_unverified_source(self):
        d=self.fixture(); d['source_verified']=False; self.assertIsNone(calculate_domain_progress(d))
    def test_missing_domain_denominator(self):
        d=self.fixture(); d['phases'][2]['requirements'][0]['domain']='governance_documentation'; d['phases'][6]['requirements'][0]['domain']='governance_documentation'; self.assertIsNone(calculate_domain_progress(d))
    def test_missing_approval(self):
        d=self.fixture(); d['phases'][0]['requirements'][0]['human_accepted']=False; self.assertIsNone(calculate_domain_progress(d))
    def test_duplicate_ids(self):
        d=self.fixture(); d['phases'][1]['requirements'][0]['id']='r1'; self.assertIsNone(calculate_domain_progress(d))
    def test_bad_weight(self):
        d=self.fixture(); d['phases'][0]['weight']=float('nan'); self.assertIsNone(calculate_domain_progress(d))
    def test_missing_phase(self):
        d=self.fixture(); d['phases'].pop(); self.assertIsNone(calculate_domain_progress(d))
    def test_boolean_completed(self):
        d=self.fixture(); d['phases'][0]['requirements'][0]['completed']='true'; self.assertIsNone(calculate_domain_progress(d))

if __name__ == '__main__': unittest.main()
