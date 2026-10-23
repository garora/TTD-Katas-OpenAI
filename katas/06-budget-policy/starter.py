"""Starter implementation for Kata 06: Keep Budget and Delivery Policy Deterministic."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Decision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"


class ReasonCode(StrEnum):
    BUDGET_EXCEEDED = "budget_exceeded"
    LEAD_TIME_EXCEEDED = "lead_time_exceeded"


@dataclass(frozen=True)
class Quote:
    sku: str
    quantity: int
    unit_price_usd: int
    lead_days: int

    @property
    def total_usd(self) -> int:
        return self.quantity * self.unit_price_usd


@dataclass(frozen=True)
class ProcurementPolicy:
    budget_usd: int
    max_lead_days: int


@dataclass(frozen=True)
class PolicyReason:
    code: ReasonCode
    field: str
    observed: int
    limit: int


@dataclass(frozen=True)
class PolicyDecision:
    decision: Decision
    reasons: tuple[PolicyReason, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "decision": self.decision.value,
            "reasons": [
                {"code": reason.code.value, "field": reason.field, "observed": reason.observed, "limit": reason.limit}
                for reason in self.reasons
            ],
        }


def evaluate_quote(quote: Quote, policy: ProcurementPolicy) -> PolicyDecision:
    """Apply deterministic procurement constraints.

    TODO: validate model inputs, evaluate budget and delivery separately, and
    return a structured decision without asking a model for policy judgment.
    """
    raise NotImplementedError("Implement one test at a time")
