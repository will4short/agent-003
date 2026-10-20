"""Lesson 21: offline token accounting and an estimated per-process budget.

Rates are user-supplied USD per million tokens; never assume model pricing.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import os


def _amount(name, default=None):
    raw = os.environ.get(name, default)
    if raw is None:
        raise ValueError(f"Set {name} to the current USD-per-million-token rate")
    try:
        value = Decimal(str(raw))
    except InvalidOperation as exc:
        raise ValueError(f"Invalid {name}") from exc
    if not value.is_finite() or value < 0:
        raise ValueError(f"Invalid {name}: must be nonnegative and finite")
    return value


@dataclass
class CostGuard:
    budget: Decimal
    input_rate: Decimal
    output_rate: Decimal
    cached_input_rate: Decimal
    warning_fraction: Decimal = Decimal('0.75')
    spent: Decimal = Decimal('0')
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    warned: bool = False

    @classmethod
    def from_environment(cls):
        budget = _amount('AGENT_SESSION_BUDGET_USD', '0.20')
        if budget <= 0:
            raise ValueError('AGENT_SESSION_BUDGET_USD must be greater than zero')
        return cls(budget, _amount('AGENT_INPUT_USD_PER_M'),
                   _amount('AGENT_OUTPUT_USD_PER_M'),
                   _amount('AGENT_CACHED_INPUT_USD_PER_M'))

    def ensure_can_request(self):
        if self.spent >= self.budget:
            raise BudgetExceeded(f'Estimated session budget reached: ${self.spent:.4f} / ${self.budget:.2f}')

    def record(self, response):
        usage = getattr(response, 'usage', None)
        if usage is None:
            print('COST WARNING: Response has no usage data; budget estimate may be understated.')
            return
        inp = int(getattr(usage, 'input_tokens', 0) or 0)
        out = int(getattr(usage, 'output_tokens', 0) or 0)
        details = getattr(usage, 'input_tokens_details', None)
        cached = int(getattr(details, 'cached_tokens', 0) or 0)
        if min(inp, out, cached) < 0 or cached > inp:
            print('COST WARNING: Invalid usage fields; skipping estimate.')
            return
        delta = ((Decimal(inp - cached) * self.input_rate)
                 + (Decimal(cached) * self.cached_input_rate)
                 + (Decimal(out) * self.output_rate)) / Decimal(1_000_000)
        self.spent += delta
        self.requests += 1
        self.input_tokens += inp
        self.output_tokens += out
        self.cached_input_tokens += cached
        print(f'COST: request {self.requests}; estimated session ${self.spent:.4f} / ${self.budget:.2f}')
        if self.spent >= self.budget * self.warning_fraction and not self.warned:
            self.warned = True
            print('COST WARNING: Session has reached at least 75% of estimated budget.')

    def summary(self):
        return (f'API COST SUMMARY: {self.requests} responses; input={self.input_tokens}, '
                f'cached_input={self.cached_input_tokens}, output={self.output_tokens}; '
                f'estimated ${self.spent:.4f} / ${self.budget:.2f} (USD). '
                'Estimate only; requests can overshoot the budget.')


class BudgetExceeded(RuntimeError):
    pass
