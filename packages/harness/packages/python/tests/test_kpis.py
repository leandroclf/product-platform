import json
import math
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


class KpiNativeBoundaryTests(unittest.TestCase):
    """Values JSON cannot carry must still fail closed, never become empty or zero."""

    evidence = {'windowStart': '2026-10-01T00:00:00Z', 'windowEnd': '2026-11-01T00:00:00Z',
                'source': 'fixture-only', 'coverage': 'complete'}

    def test_public_package_export(self):
        import product_platform_harness
        self.assertIn('calculate_kpi', product_platform_harness.__all__)
        self.assertIs(product_platform_harness.calculate_kpi, calculate_kpi)

    def test_non_json_numbers_and_shapes_are_rejected(self):
        for value in (float('nan'), float('inf'), float('-inf'), 2**53, 1.5, True, '1', b'1'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                calculate_kpi({'kind': 'acceptance_rate', 'accepted': value, 'submitted': 4}, self.evidence)
        for durations in ({}, '', 0, set(), frozenset(), b'', [float('inf')], [float('nan')], [2**53]):
            with self.subTest(durations=durations), self.assertRaises(ValueError):
                calculate_kpi({'kind': 'lead_time_ms', 'durationsMs': durations}, self.evidence)
        for evidence in ({**self.evidence, 'windowStart': None}, {**self.evidence, 'source': None},
                         {**self.evidence, 'source': b'x'}, {**self.evidence, 'coverage': None}):
            with self.subTest(evidence=evidence), self.assertRaises(ValueError):
                calculate_kpi({'kind': 'lead_time_ms', 'durationsMs': [1]}, evidence)
        for args in ((None, self.evidence), ({'kind': 'lead_time_ms', 'durationsMs': [1]}, None)):
            with self.assertRaises(ValueError):
                calculate_kpi(*args)

    def test_integral_floats_and_negative_zero_match_typescript_numbers(self):
        self.assertEqual(calculate_kpi({'kind': 'lead_time_ms', 'durationsMs': (1.0, 2)}, self.evidence)['value'], 1.5)
        margin = calculate_kpi({'kind': 'contribution_margin_minor', 'netRevenueMinor': -0.0,
                                'variableCostMinor': 0, 'currency': 'BRL'}, self.evidence)['value']
        self.assertEqual(math.copysign(1, margin), 1.0)
        self.assertEqual(calculate_kpi({'kind': 'lead_time_ms', 'durationsMs': [2**53 - 1]}, self.evidence)['value'],
                         2**53 - 1)
        with self.assertRaises(ValueError):
            calculate_kpi({'kind': 'lead_time_ms', 'durationsMs': [2**53 - 1, 1]}, self.evidence)


if __name__ == '__main__':
    unittest.main()
