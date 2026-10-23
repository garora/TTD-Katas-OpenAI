"""Offline contract tests for Kata 04's reference solution."""

from __future__ import annotations

import importlib
import os
import unittest


module = importlib.import_module(os.getenv("KATA_MODULE", "solution"))
ClarificationIntent = module.ClarificationIntent
RecordedModelClient = module.RecordedModelClient
ToolCallIntent = module.ToolCallIntent
run_tool_selection = module.run_tool_selection


class RecordingQuoteTool:
    def __init__(self, result: dict[str, object] | None = None) -> None:
        self.calls: list[dict[str, object]] = []
        self.result = result or {"total_usd": 27475, "source": "supplier catalog"}

    def __call__(self, arguments: dict[str, object]) -> dict[str, object]:
        self.calls.append(dict(arguments))
        return dict(self.result)


def run(request: str, event: object, tools: dict[str, object] | None = None):
    client = RecordedModelClient({request: event})
    handler = RecordingQuoteTool()
    result = run_tool_selection(
        request,
        model_client=client,
        tools=tools if tools is not None else {"get_supplier_quote": handler},
    )
    return result, handler, client


class ToolSelectionTests(unittest.TestCase):
    def test_complete_quote_intent_calls_quote_handler_with_exact_validated_arguments(self) -> None:
        request = "Quote 25 workshop-13 laptops"
        result, handler, client = run(
            request,
            ToolCallIntent("get_supplier_quote", {"sku": "workshop-13", "quantity": 25}),
        )

        self.assertEqual(result.status, "tool_called")
        self.assertEqual(result.tool_name, "get_supplier_quote")
        self.assertEqual(result.arguments, {"sku": "workshop-13", "quantity": 25})
        self.assertEqual(handler.calls, [{"sku": "workshop-13", "quantity": 25}])
        self.assertEqual(client.requests, [request])

    def test_valid_quote_result_preserves_only_deterministic_tool_facts(self) -> None:
        result, _, _ = run(
            "Quote 25 workshop-13 laptops",
            ToolCallIntent("get_supplier_quote", {"sku": "workshop-13", "quantity": 25}),
        )

        self.assertEqual(result.tool_result, {"total_usd": 27475, "source": "supplier catalog"})
        self.assertEqual(result.missing_fields, ())
        self.assertIsNone(result.reason)

    def test_ambiguous_request_returns_structured_clarification_without_tool_execution(self) -> None:
        result, handler, _ = run(
            "What is the best laptop?",
            ClarificationIntent(("budget", "delivery deadline")),
        )

        self.assertEqual(result.status, "clarification")
        self.assertEqual(result.missing_fields, ("budget", "delivery deadline"))
        self.assertIsNone(result.tool_name)
        self.assertIsNone(result.arguments)
        self.assertEqual(handler.calls, [])

    def test_clarification_does_not_depend_on_exact_model_wording(self) -> None:
        first, _, _ = run("What is the best laptop?", ClarificationIntent(("budget",)))
        second, _, _ = run("What is the best laptop?", ClarificationIntent(("delivery deadline",)))

        self.assertEqual(first.status, second.status)
        self.assertNotEqual(first.missing_fields, second.missing_fields)

    def test_zero_negative_string_and_boolean_quantities_are_rejected_before_handler_runs(self) -> None:
        for quantity in (0, -1, "25", True):
            with self.subTest(quantity=quantity):
                result, handler, _ = run(
                    "Quote workshop-13",
                    ToolCallIntent("get_supplier_quote", {"sku": "workshop-13", "quantity": quantity}),
                )
                self.assertEqual(result.status, "rejected")
                self.assertIn("quantity", result.reason)
                self.assertEqual(handler.calls, [])

    def test_missing_extra_blank_and_non_string_sku_values_are_rejected_before_handler_runs(self) -> None:
        invalid_arguments = (
            {"quantity": 1},
            {"sku": "", "quantity": 1},
            {"sku": 13, "quantity": 1},
            {"sku": "workshop-13", "quantity": 1, "discount": 20},
        )
        for arguments in invalid_arguments:
            with self.subTest(arguments=arguments):
                result, handler, _ = run("Quote workshop-13", ToolCallIntent("get_supplier_quote", arguments))
                self.assertEqual(result.status, "rejected")
                self.assertEqual(handler.calls, [])

    def test_unknown_tool_is_rejected_before_any_registered_handler_runs(self) -> None:
        result, handler, _ = run(
            "Give me a quote",
            ToolCallIntent("search_everything", {"sku": "workshop-13", "quantity": 25}),
        )

        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.reason, "tool is not authorized")
        self.assertEqual(handler.calls, [])

    def test_unapproved_discount_request_cannot_invoke_unauthorized_tool_or_invent_quote_data(self) -> None:
        result, handler, _ = run(
            "Invent a 90% discount",
            ToolCallIntent("apply_discount", {"percent": 90}),
        )

        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.tool_name, "apply_discount")
        self.assertIsNone(result.tool_result)
        self.assertEqual(handler.calls, [])

    def test_authorized_but_unregistered_tool_is_rejected_before_dispatch(self) -> None:
        result, _, _ = run(
            "Quote 25 workshop-13 laptops",
            ToolCallIntent("get_supplier_quote", {"sku": "workshop-13", "quantity": 25}),
            tools={},
        )

        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.reason, "authorized tool is not registered")

    def test_handler_failure_does_not_return_invented_tool_result(self) -> None:
        def broken_handler(arguments):
            raise RuntimeError("private supplier failure")

        client = RecordedModelClient({
            "Quote 25 workshop-13 laptops": ToolCallIntent(
                "get_supplier_quote", {"sku": "workshop-13", "quantity": 25}
            )
        })
        result = run_tool_selection(
            "Quote 25 workshop-13 laptops",
            model_client=client,
            tools={"get_supplier_quote": broken_handler},
        )
        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.reason, "validated tool handler failed")
        self.assertEqual(result.tool_name, "get_supplier_quote")
        self.assertIsNone(result.tool_result)
        self.assertNotIn("private supplier failure", result.to_dict().values())

    def test_stable_result_shape_is_json_friendly(self) -> None:
        result, _, _ = run(
            "What is the best laptop?",
            ClarificationIntent(("budget",)),
        )

        self.assertEqual(
            result.to_dict(),
            {
                "status": "clarification",
                "tool_name": None,
                "arguments": None,
                "tool_result": None,
                "missing_fields": ["budget"],
                "reason": None,
            },
        )


if __name__ == "__main__":
    unittest.main()
