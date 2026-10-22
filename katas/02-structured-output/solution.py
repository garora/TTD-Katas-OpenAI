"""Reference solution for Kata 02: Validate Structured Model Output."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import StrEnum


class Decision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    NEEDS_CLARIFICATION = "needs_clarification"


class RecommendationValidationError(ValueError):
    """Raised when a response cannot satisfy the application contract."""


@dataclass(frozen=True)
class Recommendation:
    sku: str
    total_usd: int
    lead_days: int
    decision: Decision
    uncertainties: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation for downstream code."""
        result = asdict(self)
        result["decision"] = self.decision.value
        result["uncertainties"] = list(self.uncertainties)
        return result


def _parse_payload(payload: str | Mapping[str, object]) -> Mapping[str, object]:
    if isinstance(payload, str):
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as error:
            raise RecommendationValidationError("payload must be valid JSON") from error
    elif isinstance(payload, Mapping):
        parsed = dict(payload)
    else:
        raise RecommendationValidationError("payload must be a JSON string or mapping")

    if not isinstance(parsed, Mapping):
        raise RecommendationValidationError("payload must decode to a JSON object")
    return parsed


def _required_text(payload: Mapping[str, object], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise RecommendationValidationError(f"{field} must be a non-blank string")
    return value.strip()


def _non_negative_integer(payload: Mapping[str, object], field: str) -> int:
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RecommendationValidationError(f"{field} must be a non-negative integer")
    return value


def _decision(payload: Mapping[str, object]) -> Decision:
    value = payload.get("decision")
    try:
        return Decision(value)
    except (TypeError, ValueError) as error:
        allowed = ", ".join(item.value for item in Decision)
        raise RecommendationValidationError(
            f"decision must be one of: {allowed}"
        ) from error


def _uncertainties(payload: Mapping[str, object]) -> tuple[str, ...]:
    value = payload.get("uncertainties")
    if not isinstance(value, list):
        raise RecommendationValidationError("uncertainties must be a list of non-blank strings")

    normalized: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise RecommendationValidationError(
                f"uncertainties[{index}] must be a non-blank string"
            )
        normalized.append(item.strip())
    return tuple(normalized)


def parse_recommendation(payload: str | Mapping[str, object]) -> Recommendation:
    """Parse an untrusted response into a validated typed recommendation."""
    data = _parse_payload(payload)
    return Recommendation(
        sku=_required_text(data, "sku"),
        total_usd=_non_negative_integer(data, "total_usd"),
        lead_days=_non_negative_integer(data, "lead_days"),
        decision=_decision(data),
        uncertainties=_uncertainties(data),
    )
