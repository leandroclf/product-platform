import json
from pathlib import Path
import unittest

from product_platform_harness import calculate_kpi


class KpiContractTests(unittest.TestCase):
    def test_shared_contract(self):
        fixtures = Path(__file__).resolve().parents[3] / 'fixtures' / 'kpi-cases.json'
        cases = json.loads(fixtures.read_text(encoding='utf-8'))
        default = {'windowStart': '2026-10-01T00:00:00Z', 'windowEnd': '2026-11-01T00:00:00Z',
                   'source': 'fixture-only', 'coverage': 'complete'}
        for case in cases:
            with self.subTest(case=case['name']):
                evidence = {**default, **case.get('evidence', {})}
                if case.get('error'):
                    with self.assertRaises(ValueError):
                        calculate_kpi(case['input'], evidence)
                else:
                    result = calculate_kpi(case['input'], evidence)
                    self.assertEqual(result['kind'], case['input']['kind'])
                    self.assertEqual(result['value'], case['value'])
                    self.assertEqual(result['reason'], case['reason'])
                    self.assertEqual(result['coverage'], evidence['coverage'])
                    self.assertEqual(result['windowStart'], evidence['windowStart'])
                    self.assertEqual(result['windowEnd'], evidence['windowEnd'])
                    self.assertEqual(result['source'], evidence['source'])
                    self.assertEqual(result['kind'], case['input']['kind'])
                    self.assertEqual(result.get('currency'), case.get('currency'))


if __name__ == '__main__':
    unittest.main()
