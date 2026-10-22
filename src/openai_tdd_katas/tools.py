"""Validated deterministic tools used by kata orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .contracts import SupplierQuote


class ToolInputError(ValueError):
    """Raised when incoming tool arguments do not satisfy the tool contract."""


class UnknownSkuError(ToolInputError):
    """Raised when a requested SKU does not exist in the local catalog."""


@dataclass(frozen=True)
class CatalogItem:
    unit_price_usd: int
    lead_days: int


CATALOG: dict[str, CatalogItem] = {
    "workshop-13": CatalogItem(unit_price_usd=1099, lead_days=7),
    "workshop-14": CatalogItem(unit_price_usd=1399, lead_days=10),
    "workshop-pro": CatalogItem(unit_price_usd=1899, lead_days=14),
}


def _valid_sku(arguments: Mapping[str, object]) -> str:
    sku = arguments.get("sku")
    if not isinstance(sku, str) or not sku.strip():
        raise ToolInputError("sku must be a non-blank string")
    return sku.strip()


def _valid_quantity(arguments: Mapping[str, object]) -> int:
    quantity = arguments.get("quantity")
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise ToolInputError("quantity must be a positive integer")
    return quantity


def get_supplier_quote(arguments: Mapping[str, object]) -> SupplierQuote:
    """Return a deterministic quote from an in-memory supplier catalog."""
    if not isinstance(arguments, Mapping):
        raise ToolInputError("arguments must be a mapping")

    sku = _valid_sku(arguments)
    quantity = _valid_quantity(arguments)
    try:
        item = CATALOG[sku]
    except KeyError as error:
        raise UnknownSkuError(f"unknown sku: {sku}") from error

    return SupplierQuote(
        sku=sku,
        quantity=quantity,
        unit_price_usd=item.unit_price_usd,
        total_usd=item.unit_price_usd * quantity,
        lead_days=item.lead_days,
    )
