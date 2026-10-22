"""Offline unit tests for Kata 03's reference solution."""

from __future__ import annotations

import importlib
import json
import os
import unittest


module = importlib.import_module(os.getenv("KATA_MODULE", "solution"))
CATALOG = module.CATALOG
ToolInputError = module.ToolInputError
UnknownSkuError = module.UnknownSkuError
get_supplier_quote = module.get_supplier_quote


class SupplierQuoteToolTests(unittest.TestCase):
    def test_quote_for_one_known_sku_contains_the_documented_fields(self) -> None:
        quote = get_supplier_quote({"sku": "workshop-13", "quantity": 1})

        self.assertEqual(
            quote,
            {
                "sku": "workshop-13",
                "quantity": 1,
                "unit_price_usd": 1099,
                "total_usd": 1099,
                "lead_days": 7,
                "source": "supplier catalog",
            },
        )

    def test_quote_for_25_workshop_13_units_has_expected_total_and_lead_time(self) -> None:
        quote = get_supplier_quote({"sku": "workshop-13", "quantity": 25})

        self.assertEqual(quote["total_usd"], 27475)
        self.assertEqual(quote["lead_days"], 7)
        self.assertEqual(quote["source"], "supplier catalog")

    def test_total_is_unit_price_times_quantity_for_every_catalog_item(self) -> None:
        for sku, item in CATALOG.items():
            with self.subTest(sku=sku):
                quote = get_supplier_quote({"sku": sku, "quantity": 3})
                self.assertEqual(quote["total_usd"], item.unit_price_usd * 3)

    def test_known_skus_keep_their_own_lead_times(self) -> None:
        self.assertEqual(get_supplier_quote({"sku": "workshop-14", "quantity": 1})["lead_days"], 10)
        self.assertEqual(get_supplier_quote({"sku": "workshop-pro", "quantity": 1})["lead_days"], 14)

    def test_zero_and_negative_quantities_are_rejected_before_calculation(self) -> None:
        for quantity in (0, -1):
            with self.subTest(quantity=quantity):
                with self.assertRaisesRegex(ToolInputError, "quantity"):
                    get_supplier_quote({"sku": "workshop-13", "quantity": quantity})

    def test_non_integer_and_boolean_quantities_are_rejected(self) -> None:
        for quantity in ("25", 2.5, True):
            with self.subTest(quantity=quantity):
                with self.assertRaisesRegex(ToolInputError, "quantity"):
                    get_supplier_quote({"sku": "workshop-13", "quantity": quantity})

    def test_missing_blank_and_non_string_skus_are_rejected(self) -> None:
        for sku in (None, "", "   ", 13):
            with self.subTest(sku=sku):
                arguments = {"quantity": 1}
                if sku is not None:
                    arguments["sku"] = sku
                with self.assertRaisesRegex(ToolInputError, "sku"):
                    get_supplier_quote(arguments)

    def test_unknown_sku_raises_a_typed_error(self) -> None:
        with self.assertRaisesRegex(UnknownSkuError, "unknown sku: workshop-404"):
            get_supplier_quote({"sku": "workshop-404", "quantity": 1})

    def test_arguments_must_be_a_mapping(self) -> None:
        with self.assertRaisesRegex(ToolInputError, "mapping"):
            get_supplier_quote([("sku", "workshop-13")])  # type: ignore[arg-type]

    def test_response_is_json_serializable_and_has_stable_provenance(self) -> None:
        quote = get_supplier_quote({"sku": "workshop-13", "quantity": 25})
        encoded = json.dumps(quote)

        self.assertEqual(json.loads(encoded), quote)
        self.assertEqual(quote["source"], "supplier catalog")


if __name__ == "__main__":
    unittest.main()
