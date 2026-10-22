"""Reference solution for Kata 03: Deterministic Supplier Quote Tool."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


class ToolInputError(ValueError):
    """Raised when tool-call arguments do not match the tool contract."""


class UnknownSkuError(ToolInputError):
    """Raised when a validated SKU does not exist in the local catalog."""


@dataclass(frozen=True)
class CatalogItem:
    unit_price_usd: int
    lead_days: int


CATALOG: dict[str, CatalogItem] = {
    "workshop-13": CatalogItem(unit_price_usd=1099, lead_days=7),
    "workshop-14": CatalogItem(unit_price_usd=1399, lead_days=10),
    "workshop-pro": CatalogItem(unit_price_usd=1899, lead_days=14),
}


def _arguments_mapping(arguments: Mapping[str, object]) -> Mapping[str, object]:
    if not isinstance(arguments, Mapping):
        raise ToolInputError("arguments must be a mapping")
    return arguments


def _sku(arguments: Mapping[str, object]) -> str:
    value = arguments.get("sku")
    if not isinstance(value, str) or not value.strip():
        raise ToolInputError("sku must be a non-blank string")
    return value.strip()


def _quantity(arguments: Mapping[str, object]) -> int:
    value = arguments.get("quantity")
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ToolInputError("quantity must be a positive integer")
    return value


def get_supplier_quote(arguments: Mapping[str, object]) -> dict[str, object]:
    """Return a validated, deterministic quote from the local catalog."""
    data = _arguments_mapping(arguments)
    sku = _sku(data)
    quantity = _quantity(data)

    try:
        item = CATALOG[sku]
    except KeyError as error:
        raise UnknownSkuError(f"unknown sku: {sku}") from error

    return {
        "sku": sku,
        "quantity": quantity,
        "unit_price_usd": item.unit_price_usd,
        "total_usd": item.unit_price_usd * quantity,
        "lead_days": item.lead_days,
        "source": "supplier catalog",
    }
