"""Lesson 21: Offline API token accounting and cost monitoring.

Agent 003 operates without an enforced session spending limit.

API usage and estimated costs are still tracked and reported.

Pricing rates are supplied through environment variables in USD
per million tokens. Never assume model pricing.

IMPORTANT:
Disabling the agent's internal budget does not disable API billing.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import os


def _amount(name, default=None):
    """Read and validate a nonnegative decimal environment variable."""

    raw = os.environ.get(name, default)

    if raw is None:
        raise ValueError(
            f"Set {name} to the current USD-per-million-token rate"
        )

    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid {name}") from exc

    if not value.is_finite() or value < 0:
        raise ValueError(
            f"Invalid {name}: must be nonnegative and finite"
        )

    return value


@dataclass
class CostGuard:
    """Track estimated API spending without enforcing a session limit."""

    # Retained for compatibility with existing Agent 003 code.
    # This value is NOT used to restrict API requests.
    budget: Decimal

    input_rate: Decimal
    output_rate: Decimal
    cached_input_rate: Decimal

    # Retained for compatibility with existing code and tests.
    warning_fraction: Decimal = Decimal("0.75")

    # Session usage statistics.
    spent: Decimal = Decimal("0")
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0

    # Retained for compatibility.
    warned: bool = False

    @classmethod
    def from_environment(cls):
        """Initialize cost tracking from environment variables."""

        # Kept for backward compatibility.
        # No spending restriction is enforced.
        budget = _amount(
            "AGENT_SESSION_BUDGET_USD",
            "0.20"
        )

        input_rate = _amount(
            "AGENT_INPUT_USD_PER_M"
        )

        output_rate = _amount(
            "AGENT_OUTPUT_USD_PER_M"
        )

        cached_input_rate = _amount(
            "AGENT_CACHED_INPUT_USD_PER_M"
        )

        return cls(
            budget=budget,
            input_rate=input_rate,
            output_rate=output_rate,
            cached_input_rate=cached_input_rate,
        )

    def ensure_can_request(self):
        """Allow API requests without an internal spending limit."""

        return

    def record(self, response):
        """Record token usage and estimate API spending."""

        usage = getattr(response, "usage", None)

        if usage is None:
            print(
                "COST WARNING: Response has no usage data; "
                "spending estimate may be understated."
            )
            return

        inp = int(
            getattr(usage, "input_tokens", 0) or 0
        )

        out = int(
            getattr(usage, "output_tokens", 0) or 0
        )

        details = getattr(
            usage,
            "input_tokens_details",
            None
        )

        cached = int(
            getattr(details, "cached_tokens", 0) or 0
        )

        if min(inp, out, cached) < 0 or cached > inp:
            print(
                "COST WARNING: Invalid usage fields; "
                "skipping estimate."
            )
            return

        # Calculate estimated spending using Decimal arithmetic.
        uncached_input = inp - cached

        input_cost = (
            Decimal(uncached_input) * self.input_rate
        )

        cached_input_cost = (
            Decimal(cached) * self.cached_input_rate
        )

        output_cost = (
            Decimal(out) * self.output_rate
        )

        delta = (
            input_cost
            + cached_input_cost
            + output_cost
        ) / Decimal("1000000")

        # Update cumulative session statistics.
        self.spent += delta

        self.requests += 1

        self.input_tokens += inp

        self.output_tokens += out

        self.cached_input_tokens += cached

        # Display cost information without budget warnings.
        print(
            f"COST: request {self.requests}; "
            f"estimated request ${delta:.4f}; "
            f"estimated session spending ${self.spent:.4f}"
        )

    def summary(self):
        """Return a summary of API usage and estimated spending."""

        return (
            f"API COST SUMMARY: "
            f"{self.requests} responses; "
            f"input={self.input_tokens}, "
            f"cached_input={self.cached_input_tokens}, "
            f"output={self.output_tokens}; "
            f"estimated spending ${self.spent:.4f} (USD). "
            f"Cost tracking only; "
            f"no session spending limit is enforced."
        )


class BudgetExceeded(RuntimeError):
    """Legacy exception retained for compatibility.

    This exception is no longer raised by CostGuard.
    """

    pass