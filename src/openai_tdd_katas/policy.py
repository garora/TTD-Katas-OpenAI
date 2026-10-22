"""Deterministic business and safety rules for the kata package."""

from __future__ import annotations

from collections.abc import Collection

from .contracts import Decision, PolicyDecision, ProcurementRequirements, SupplierQuote


class ToolPermissionError(PermissionError):
    """Raised when orchestration attempts to invoke a tool outside its allow-list."""


def evaluate_quote(quote: SupplierQuote, requirements: ProcurementRequirements) -> PolicyDecision:
    """Evaluate a quote without delegating budget/deadline policy to a model."""
    reasons: list[str] = []
    if quote.total_usd > requirements.budget_usd:
        reasons.append(
            f"total ${quote.total_usd} exceeds budget ${requirements.budget_usd}"
        )
    if quote.lead_days > requirements.max_lead_days:
        reasons.append(
            f"lead time {quote.lead_days} days exceeds limit {requirements.max_lead_days} days"
        )

    if reasons:
        return PolicyDecision(decision=Decision.REJECT, reasons=tuple(reasons))
    return PolicyDecision(decision=Decision.APPROVE)


def ensure_tool_allowed(tool_name: str, allowed_tools: Collection[str]) -> None:
    """Enforce an application-owned capability allow-list."""
    if not isinstance(tool_name, str) or not tool_name.strip():
        raise ToolPermissionError("tool name must be a non-blank string")
    if tool_name not in allowed_tools:
        raise ToolPermissionError(f"tool is not allowed: {tool_name}")
