"""Reference solution for Kata 06: Keep Budget and Delivery Policy Deterministic."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Decision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"


class ReasonCode(StrEnum):
    BUDGET_EXCEEDED = "budget_exceeded"
    LEAD_TIME_EXCEEDED = "lead_time_exceeded"


def _non_blank_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-blank string")
    return value.strip()


def _non_negative_integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _positive_integer(value: object, field: str) -> int:
    result = _non_negative_integer(value, field)
    if result == 0:
        raise ValueError(f"{field} must be a positive integer")
    return result


@dataclass(frozen=True)
class Quote:
    sku: str
    quantity: int
    unit_price_usd: int
    lead_days: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "sku", _non_blank_text(self.sku, "sku"))
        _positive_integer(self.quantity, "quantity")
        _non_negative_integer(self.unit_price_usd, "unit_price_usd")
        _non_negative_integer(self.lead_days, "lead_days")

    @property
    def total_usd(self) -> int:
        return self.quantity * self.unit_price_usd


@dataclass(frozen=True)
class ProcurementPolicy:
    budget_usd: int
    max_lead_days: int

    def __post_init__(self) -> None:
        _non_negative_integer(self.budget_usd, "budget_usd")
        _non_negative_integer(self.max_lead_days, "max_lead_days")


@dataclass(frozen=True)
class PolicyReason:
    code: ReasonCode
    field: str
    observed: int
    limit: int

    def __post_init__(self) -> None:
        if not isinstance(self.code, ReasonCode):
            raise ValueError("code must be a ReasonCode")
        object.__setattr__(self, "field", _non_blank_text(self.field, "field"))
        _non_negative_integer(self.observed, "observed")
        _non_negative_integer(self.limit, "limit")


@dataclass(frozen=True)
class PolicyDecision:
    decision: Decision
    reasons: tuple[PolicyReason, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.decision, Decision):
            raise ValueError("decision must be a Decision")
        if not all(isinstance(reason, PolicyReason) for reason in self.reasons):
            raise ValueError("reasons must contain PolicyReason values")
        object.__setattr__(self, "reasons", tuple(self.reasons))

    def to_dict(self) -> dict[str, object]:
        return {
            "decision": self.decision.value,
            "reasons": [
                {"code": reason.code.value, "field": reason.field, "observed": reason.observed, "limit": reason.limit}
                for reason in self.reasons
            ],
        }


def _reason(code: ReasonCode, field: str, observed: int, limit: int) -> PolicyReason:
    return PolicyReason(code=code, field=field, observed=observed, limit=limit)


def evaluate_quote(quote: Quote, policy: ProcurementPolicy) -> PolicyDecision:
    """Evaluate already-validated facts using deterministic policy only."""
    if not isinstance(quote, Quote):
        raise TypeError("quote must be a Quote")
    if not isinstance(policy, ProcurementPolicy):
        raise TypeError("policy must be a ProcurementPolicy")

    reasons: list[PolicyReason] = []
    if quote.total_usd > policy.budget_usd:
        reasons.append(
            _reason(ReasonCode.BUDGET_EXCEEDED, "total_usd", quote.total_usd, policy.budget_usd)
        )
    if quote.lead_days > policy.max_lead_days:
        reasons.append(
            _reason(ReasonCode.LEAD_TIME_EXCEEDED, "lead_days", quote.lead_days, policy.max_lead_days)
        )

    if reasons:
        return PolicyDecision(decision=Decision.REJECT, reasons=tuple(reasons))
    return PolicyDecision(decision=Decision.APPROVE)
