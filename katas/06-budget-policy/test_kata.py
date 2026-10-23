"""Offline contract tests for Kata 06's deterministic policy evaluator."""

from __future__ import annotations

import importlib
import os
import unittest


module = importlib.import_module(os.getenv("KATA_MODULE", "solution"))
Decision = module.Decision
PolicyDecision = module.PolicyDecision
ProcurementPolicy = module.ProcurementPolicy
Quote = module.Quote
ReasonCode = module.ReasonCode
evaluate_quote = module.evaluate_quote


def quote(total_price: int, lead_days: int, quantity: int = 1) -> Quote:
    return Quote(
        sku="workshop-13",
        quantity=quantity,
        unit_price_usd=total_price // quantity,
        lead_days=lead_days,
    )


class BudgetPolicyTests(unittest.TestCase):
    def test_approves_quote_within_budget_and_deadline(self) -> None:
        result = evaluate_quote(quote(27_475, 7, quantity=25), ProcurementPolicy(30_000, 10))

        self.assertEqual(result, PolicyDecision(decision=Decision.APPROVE))
        self.assertEqual(result.reasons, ())

    def test_exact_budget_and_exact_deadline_are_approved(self) -> None:
        result = evaluate_quote(quote(30_000, 10), ProcurementPolicy(30_000, 10))

        self.assertEqual(result.decision, Decision.APPROVE)

    def test_rejects_quote_over_budget_with_structured_reason(self) -> None:
        result = evaluate_quote(quote(30_001, 7), ProcurementPolicy(30_000, 10))

        self.assertEqual(result.decision, Decision.REJECT)
        self.assertEqual(
            result.reasons,
            (module.PolicyReason(ReasonCode.BUDGET_EXCEEDED, "total_usd", 30_001, 30_000),),
        )

    def test_rejects_quote_beyond_delivery_deadline_with_structured_reason(self) -> None:
        result = evaluate_quote(quote(27_475, 11), ProcurementPolicy(30_000, 10))

        self.assertEqual(result.decision, Decision.REJECT)
        self.assertEqual(
            result.reasons,
            (module.PolicyReason(ReasonCode.LEAD_TIME_EXCEEDED, "lead_days", 11, 10),),
        )

    def test_reports_budget_then_deadline_reason_when_both_constraints_fail(self) -> None:
        result = evaluate_quote(quote(30_001, 11), ProcurementPolicy(30_000, 10))

        self.assertEqual(result.decision, Decision.REJECT)
        self.assertEqual([reason.code for reason in result.reasons], [ReasonCode.BUDGET_EXCEEDED, ReasonCode.LEAD_TIME_EXCEEDED])

    def test_total_is_quantity_times_unit_price_in_whole_usd(self) -> None:
        order = Quote("workshop-13", quantity=25, unit_price_usd=1099, lead_days=7)

        self.assertEqual(order.total_usd, 27_475)
        self.assertIsInstance(order.total_usd, int)

    def test_zero_price_is_supported_but_quantity_must_be_positive(self) -> None:
        self.assertEqual(Quote("trial", 1, 0, 0).total_usd, 0)
        for invalid_quantity in (0, -1, True, "1"):
            with self.subTest(invalid_quantity=invalid_quantity):
                with self.assertRaisesRegex(ValueError, "quantity"):
                    Quote("workshop-13", invalid_quantity, 1099, 7)

    def test_money_deadline_and_policy_inputs_reject_non_integer_boolean_or_negative_values(self) -> None:
        invalid_values = (-1, True, "10")
        for invalid in invalid_values:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    Quote("sku", 1, invalid, 7)
                with self.assertRaises(ValueError):
                    Quote("sku", 1, 1, invalid)
                with self.assertRaises(ValueError):
                    ProcurementPolicy(invalid, 10)
                with self.assertRaises(ValueError):
                    ProcurementPolicy(10, invalid)

    def test_quote_and_policy_type_boundaries_are_explicit(self) -> None:
        with self.assertRaisesRegex(TypeError, "quote"):
            evaluate_quote("not a quote", ProcurementPolicy(1, 1))
        with self.assertRaisesRegex(TypeError, "policy"):
            evaluate_quote(quote(1, 1), "not a policy")

    def test_decision_serializes_to_machine_readable_facts_for_a_later_explanation_layer(self) -> None:
        result = evaluate_quote(quote(30_001, 11), ProcurementPolicy(30_000, 10))

        self.assertEqual(
            result.to_dict(),
            {
                "decision": "reject",
                "reasons": [
                    {"code": "budget_exceeded", "field": "total_usd", "observed": 30_001, "limit": 30_000},
                    {"code": "lead_time_exceeded", "field": "lead_days", "observed": 11, "limit": 10},
                ],
            },
        )

    def test_decision_object_does_not_contain_model_generated_explanation_text(self) -> None:
        result = evaluate_quote(quote(1, 1), ProcurementPolicy(1, 1))

        self.assertEqual(set(result.to_dict()), {"decision", "reasons"})
        self.assertNotIn("explanation", result.to_dict())


if __name__ == "__main__":
    unittest.main()
