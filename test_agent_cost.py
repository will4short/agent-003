import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from agent_cost import CostGuard


def usage(inp, out, cached=0):
    """Create a simulated API response with token usage."""
    return SimpleNamespace(
        usage=SimpleNamespace(
            input_tokens=inp,
            output_tokens=out,
            input_tokens_details=SimpleNamespace(
                cached_tokens=cached
            ),
        )
    )


class CostGuardTests(unittest.TestCase):

    def make_guard(self):
        """Create a cost tracker using predictable test pricing."""
        return CostGuard(
            Decimal("0.20"),
            Decimal("2"),
            Decimal("10"),
            Decimal("0.5"),
        )

    def test_usage_and_cached_pricing(self):
        """Input, output, and cached tokens are priced correctly."""
        g = self.make_guard()

        g.record(usage(100000, 1000, 50000))

        self.assertEqual(g.spent, Decimal("0.135"))
        self.assertEqual(g.requests, 1)

    def test_no_budget_enforcement(self):
        """Requests remain allowed after exceeding the old budget."""
        g = self.make_guard()

        g.record(usage(100000, 10000))

        self.assertGreater(g.spent, g.budget)

        # This should not raise BudgetExceeded.
        g.ensure_can_request()

        # Further requests should still be recorded.
        g.record(usage(100000, 10000))

        self.assertEqual(g.requests, 2)
        self.assertEqual(g.spent, Decimal("0.600"))

    def test_missing_usage_does_not_crash(self):
        """Missing usage data does not corrupt cost tracking."""
        g = self.make_guard()

        g.record(SimpleNamespace(usage=None))

        self.assertEqual(g.requests, 0)
        self.assertEqual(g.spent, Decimal("0"))

    def test_invalid_usage_ignored(self):
        """Invalid cached-token counts are rejected."""
        g = self.make_guard()

        g.record(usage(1, 1, 2))

        self.assertEqual(g.spent, Decimal("0"))
        self.assertEqual(g.requests, 0)

    def test_rates_required(self):
        """Pricing configuration must contain valid rates."""
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ValueError):
                CostGuard.from_environment()

    def test_environment(self):
        """Environment configuration loads pricing correctly."""
        env = {
            "AGENT_INPUT_USD_PER_M": "2",
            "AGENT_OUTPUT_USD_PER_M": "10",
            "AGENT_CACHED_INPUT_USD_PER_M": "0.5",
        }

        with patch.dict("os.environ", env, clear=True):
            g = CostGuard.from_environment()

        self.assertEqual(g.budget, Decimal("0.20"))

    def test_spending_does_not_trigger_budget_warning(self):
        """The old budget-warning threshold is no longer enforced."""
        g = self.make_guard()

        g.record(usage(80000, 0))

        self.assertEqual(g.spent, Decimal("0.160"))
        self.assertFalse(g.warned)

        # The request is still permitted.
        g.ensure_can_request()

    def test_cost_accumulates_across_requests(self):
        """Cost tracking continues throughout a session."""
        g = self.make_guard()

        g.record(usage(100000, 1000))
        g.record(usage(100000, 1000))
        g.record(usage(100000, 1000))

        self.assertEqual(g.requests, 3)
        self.assertEqual(g.spent, Decimal("0.630"))

    def test_summary_available(self):
        """The agent can report estimated spending."""
        g = self.make_guard()

        g.record(usage(100000, 1000))

        summary = g.summary()

        self.assertIsInstance(summary, str)
        self.assertIn("0.210", summary)


if __name__ == "__main__":
    unittest.main(verbosity=2)