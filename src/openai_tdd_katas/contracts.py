"""Typed contracts shared by the OpenAI TDD kata implementations.

These models intentionally use the Python standard library. They define the
application boundary before any provider SDK or model response is involved.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum


class ContractError(ValueError):
    """Raised when a value does not satisfy an application contract."""


class Decision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    NEEDS_CLARIFICATION = "needs_clarification"


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{field_name} must be a non-blank string")
    return value.strip()


def _non_negative_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ContractError(f"{field_name} must be a non-negative integer")
    return value


@dataclass(frozen=True)
class ToolCall:
    """A validated model request to invoke a named application tool."""

    call_id: str
    name: str
    arguments: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "call_id", _required_text(self.call_id, "call_id"))
        object.__setattr__(self, "name", _required_text(self.name, "name"))
        if not isinstance(self.arguments, Mapping):
            raise ContractError("arguments must be a mapping")
        object.__setattr__(self, "arguments", dict(self.arguments))


@dataclass(frozen=True)
class ToolResult:
    """A normalized, provenance-carrying result returned by a local tool."""

    call_id: str
    name: str
    output: Mapping[str, object]
    source: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "call_id", _required_text(self.call_id, "call_id"))
        object.__setattr__(self, "name", _required_text(self.name, "name"))
        object.__setattr__(self, "source", _required_text(self.source, "source"))
        if not isinstance(self.output, Mapping):
            raise ContractError("tool output must be a mapping")
        object.__setattr__(self, "output", dict(self.output))


@dataclass(frozen=True)
class Evidence:
    """A fact source that may support a final application response."""

    evidence_id: str
    source: str
    facts: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_id", _required_text(self.evidence_id, "evidence_id"))
        object.__setattr__(self, "source", _required_text(self.source, "source"))
        if not isinstance(self.facts, Mapping):
            raise ContractError("facts must be a mapping")
        object.__setattr__(self, "facts", dict(self.facts))


@dataclass(frozen=True)
class SupplierQuote:
    """A deterministic quote suitable for policy evaluation and rendering."""

    sku: str
    quantity: int
    unit_price_usd: int
    total_usd: int
    lead_days: int
    source: str = "supplier catalog"

    def __post_init__(self) -> None:
        object.__setattr__(self, "sku", _required_text(self.sku, "sku"))
        if isinstance(self.quantity, bool) or not isinstance(self.quantity, int) or self.quantity <= 0:
            raise ContractError("quantity must be a positive integer")
        for name in ("unit_price_usd", "total_usd", "lead_days"):
            _non_negative_int(getattr(self, name), name)
        object.__setattr__(self, "source", _required_text(self.source, "source"))
        if self.total_usd != self.quantity * self.unit_price_usd:
            raise ContractError("total_usd must equal quantity multiplied by unit_price_usd")

    def to_dict(self) -> dict[str, object]:
        return {
            "sku": self.sku,
            "quantity": self.quantity,
            "unit_price_usd": self.unit_price_usd,
            "total_usd": self.total_usd,
            "lead_days": self.lead_days,
            "source": self.source,
        }


@dataclass(frozen=True)
class ProcurementRequirements:
    budget_usd: int
    max_lead_days: int

    def __post_init__(self) -> None:
        _non_negative_int(self.budget_usd, "budget_usd")
        _non_negative_int(self.max_lead_days, "max_lead_days")


@dataclass(frozen=True)
class PolicyDecision:
    decision: Decision
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.decision, Decision):
            raise ContractError("decision must be a Decision value")
        normalized = tuple(_required_text(reason, "reason") for reason in self.reasons)
        object.__setattr__(self, "reasons", normalized)


@dataclass(frozen=True)
class SessionRecord:
    chat_id: str
    session_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "chat_id", _required_text(self.chat_id, "chat_id"))
        object.__setattr__(self, "session_id", _required_text(self.session_id, "session_id"))


@dataclass(frozen=True)
class AgentResult:
    """Observable terminal result of one bounded agent turn."""

    session_id: str
    final_text: str
    tool_calls: tuple[ToolCall, ...] = field(default_factory=tuple)
    tool_results: tuple[ToolResult, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "session_id", _required_text(self.session_id, "session_id"))
        object.__setattr__(self, "final_text", _required_text(self.final_text, "final_text"))
