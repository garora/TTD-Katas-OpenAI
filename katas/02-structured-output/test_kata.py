"""Offline contract tests for Kata 02's reference solution."""

from __future__ import annotations

import importlib
import os
import unittest


module = importlib.import_module(os.getenv("KATA_MODULE", "solution"))
Decision = module.Decision
Recommendation = module.Recommendation
RecommendationValidationError = module.RecommendationValidationError
parse_recommendation = module.parse_recommendation

VALID_PAYLOAD = {
    "sku": "workshop-13",
    "total_usd": 27475,
    "lead_days": 7,
    "decision": "approve",
    "uncertainties": ["Windows edition is not yet confirmed."],
}


class StructuredOutputTests(unittest.TestCase):
    def test_valid_json_parses_to_a_typed_recommendation(self) -> None:
        result = parse_recommendation(
            '{"sku":"workshop-13","total_usd":27475,"lead_days":7,'
            '"decision":"approve","uncertainties":[]}'
        )

        self.assertEqual(
            result,
            Recommendation(
                sku="workshop-13",
                total_usd=27475,
                lead_days=7,
                decision=Decision.APPROVE,
                uncertainties=(),
            ),
        )

    def test_mapping_payload_uses_the_same_validation_path(self) -> None:
        result = parse_recommendation(VALID_PAYLOAD)

        self.assertEqual(result.sku, "workshop-13")
        self.assertEqual(result.decision, Decision.APPROVE)
        self.assertEqual(result.uncertainties, ("Windows edition is not yet confirmed.",))

    def test_invalid_json_is_rejected_with_a_useful_error(self) -> None:
        with self.assertRaisesRegex(RecommendationValidationError, "valid JSON"):
            parse_recommendation("not JSON")

    def test_json_must_decode_to_an_object(self) -> None:
        with self.assertRaisesRegex(RecommendationValidationError, "JSON object"):
            parse_recommendation("[]")

    def test_every_required_field_is_validated(self) -> None:
        for field in VALID_PAYLOAD:
            payload = dict(VALID_PAYLOAD)
            del payload[field]
            with self.subTest(field=field):
                with self.assertRaises(RecommendationValidationError):
                    parse_recommendation(payload)

    def test_numeric_fields_reject_strings_booleans_and_negative_values(self) -> None:
        invalid_values = ("27475", True, -1)
        for field in ("total_usd", "lead_days"):
            for invalid_value in invalid_values:
                payload = dict(VALID_PAYLOAD, **{field: invalid_value})
                with self.subTest(field=field, invalid_value=invalid_value):
                    with self.assertRaisesRegex(RecommendationValidationError, field):
                        parse_recommendation(payload)

    def test_decision_must_be_an_approved_value(self) -> None:
        payload = dict(VALID_PAYLOAD, decision="buy everything")

        with self.assertRaisesRegex(RecommendationValidationError, "decision must be one of"):
            parse_recommendation(payload)

    def test_uncertainties_must_be_a_list_of_non_blank_strings(self) -> None:
        invalid_uncertainties = ("none", [""], [42])
        for value in invalid_uncertainties:
            with self.subTest(value=value):
                payload = dict(VALID_PAYLOAD, uncertainties=value)
                with self.assertRaisesRegex(RecommendationValidationError, "uncertainties"):
                    parse_recommendation(payload)

    def test_values_are_normalized_and_serializable(self) -> None:
        payload = dict(VALID_PAYLOAD, sku=" workshop-13 ", uncertainties=[" needs confirmation "])
        result = parse_recommendation(payload)

        self.assertEqual(result.sku, "workshop-13")
        self.assertEqual(result.uncertainties, ("needs confirmation",))
        self.assertEqual(
            result.to_dict(),
            {
                "sku": "workshop-13",
                "total_usd": 27475,
                "lead_days": 7,
                "decision": "approve",
                "uncertainties": ["needs confirmation"],
            },
        )

    def test_free_form_text_is_not_accepted_as_a_recommendation(self) -> None:
        with self.assertRaisesRegex(RecommendationValidationError, "valid JSON"):
            parse_recommendation("I recommend workshop-13 because it is affordable.")


if __name__ == "__main__":
    unittest.main()
