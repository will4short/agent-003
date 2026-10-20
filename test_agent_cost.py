import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch
from agent_cost import CostGuard, BudgetExceeded


def usage(inp, out, cached=0):
    return SimpleNamespace(usage=SimpleNamespace(input_tokens=inp, output_tokens=out,
        input_tokens_details=SimpleNamespace(cached_tokens=cached)))

class CostGuardTests(unittest.TestCase):
    def make_guard(self):
        return CostGuard(Decimal('0.20'), Decimal('2'), Decimal('10'), Decimal('0.5'))

    def test_usage_and_cached_pricing(self):
        g = self.make_guard()
        g.record(usage(100000, 1000, 50000))
        self.assertEqual(g.spent, Decimal('0.135'))
        self.assertEqual(g.requests, 1)

    def test_blocks_at_budget(self):
        g = self.make_guard()
        g.record(usage(100000, 10000))
        with self.assertRaises(BudgetExceeded):
            g.ensure_can_request()

    def test_missing_usage_does_not_crash(self):
        g = self.make_guard()
        g.record(SimpleNamespace(usage=None))
        self.assertEqual(g.requests, 0)

    def test_invalid_usage_ignored(self):
        g = self.make_guard()
        g.record(usage(1, 1, 2))
        self.assertEqual(g.spent, 0)

    def test_rates_required(self):
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError):
                CostGuard.from_environment()

    def test_environment(self):
        env = {'AGENT_INPUT_USD_PER_M':'2', 'AGENT_OUTPUT_USD_PER_M':'10',
               'AGENT_CACHED_INPUT_USD_PER_M':'0.5'}
        with patch.dict('os.environ', env, clear=True):
            g = CostGuard.from_environment()
        self.assertEqual(g.budget, Decimal('0.20'))

    def test_warning_flag(self):
        g = self.make_guard()
        g.record(usage(80000, 0))
        self.assertTrue(g.warned)

if __name__ == '__main__':
    unittest.main(verbosity=2)
