"""Starter implementation for Kata 02: Validate Structured Model Output."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping


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


def parse_recommendation(payload: str | Mapping[str, object]) -> Recommendation:
    """Parse and validate a model-facing recommendation payload.

    TODO: support JSON strings and mappings, then validate every field before
    building `Recommendation`. Do not accept free-form text as valid output.
    """
    raise NotImplementedError("Implement this one test at a time")
