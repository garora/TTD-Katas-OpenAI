"""Starter implementation for Kata 03: Deterministic Supplier Quote Tool."""

from __future__ import annotations

from collections.abc import Mapping


class ToolInputError(ValueError):
    """Raised when tool-call arguments do not match the tool contract."""


class UnknownSkuError(ToolInputError):
    """Raised when a validated SKU does not exist in the local catalog."""


CATALOG = {
    "workshop-13": {"unit_price_usd": 1099, "lead_days": 7},
    "workshop-14": {"unit_price_usd": 1399, "lead_days": 10},
    "workshop-pro": {"unit_price_usd": 1899, "lead_days": 14},
}


def get_supplier_quote(arguments: Mapping[str, object]) -> dict[str, object]:
    """Return a validated, deterministic quote from the local catalog.

    TODO: validate the mapping, SKU, and quantity. Then calculate the total
    and return the stable response contract documented in README.md.
    """
    raise NotImplementedError("Implement this one test at a time")
