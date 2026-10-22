"""Offline unit tests for the reusable openai_tdd_katas package."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from openai_tdd_katas import (
    AgentOrchestrator,
    Decision,
    InMemorySessionStore,
    ModelRequest,
    ProcurementRequirements,
    StepLimitExceeded,
    SupplierQuote,
    TerminalEvent,
    ToolCall,
    ToolCallEvent,
    ToolExecutionError,
    ToolInputError,
    ToolPermissionError,
    UnknownSkuError,
    evaluate_quote,
    get_supplier_quote,
)


class ScriptedModelClient:
    def __init__(self, events: list[object]) -> None:
        self.events = list(events)
        self.requests: list[ModelRequest] = []
        self.continuations = []

    def start_turn(self, request: ModelRequest) -> object:
        self.requests.append(request)
        return self.events.pop(0)

    def continue_after_tool(self, session_id: str, tool_result: object) -> object:
        self.continuations.append((session_id, tool_result))
        return self.events.pop(0)


class ToolsAndPolicyTests(unittest.TestCase):
    def test_quote_is_deterministic_and_json_serializable(self) -> None:
        quote = get_supplier_quote({"sku": "workshop-13", "quantity": 25})
        self.assertEqual(quote.total_usd, 27475)
        self.assertEqual(quote.lead_days, 7)
        self.assertEqual(json.loads(json.dumps(quote.to_dict()))["source"], "supplier catalog")

    def test_quote_rejects_invalid_arguments(self) -> None:
        for arguments in (
            {"sku": "workshop-13", "quantity": 0},
            {"sku": "workshop-13", "quantity": True},
            {"sku": "", "quantity": 1},
        ):
            with self.subTest(arguments=arguments):
                with self.assertRaises(ToolInputError):
                    get_supplier_quote(arguments)

    def test_quote_rejects_unknown_sku(self) -> None:
        with self.assertRaises(UnknownSkuError):
            get_supplier_quote({"sku": "missing", "quantity": 1})

    def test_policy_approves_quote_at_budget_and_deadline_boundaries(self) -> None:
        quote = SupplierQuote("sku", 1, 100, 100, 10)
        decision = evaluate_quote(quote, ProcurementRequirements(100, 10))
        self.assertEqual(decision.decision, Decision.APPROVE)
        self.assertEqual(decision.reasons, ())

    def test_policy_rejects_budget_and_deadline_failures(self) -> None:
        quote = SupplierQuote("sku", 1, 101, 101, 11)
        decision = evaluate_quote(quote, ProcurementRequirements(100, 10))
        self.assertEqual(decision.decision, Decision.REJECT)
        self.assertEqual(len(decision.reasons), 2)


class OrchestrationTests(unittest.TestCase):
    def test_tool_loop_records_tool_call_result_and_terminal_answer(self) -> None:
        client = ScriptedModelClient([
            ToolCallEvent("event-1", ToolCall("call-1", "get_supplier_quote", {"sku": "workshop-13", "quantity": 25})),
            TerminalEvent("event-2", "The verified quote is ready."),
        ])
        orchestrator = AgentOrchestrator(model_client=client, tools={"get_supplier_quote": get_supplier_quote})

        result = orchestrator.run(chat_id="chat-1", instructions="Use tools.", user_message="Quote 25 laptops")

        self.assertEqual(result.final_text, "The verified quote is ready.")
        self.assertEqual(result.tool_calls[0].name, "get_supplier_quote")
        self.assertEqual(result.tool_results[0].output["total_usd"], 27475)
        self.assertEqual(client.continuations[0][1].source, "supplier catalog")

    def test_session_is_reused_for_follow_up_turns(self) -> None:
        client = ScriptedModelClient([
            TerminalEvent("event-1", "First answer."),
            TerminalEvent("event-2", "Second answer."),
        ])
        store = InMemorySessionStore()
        orchestrator = AgentOrchestrator(model_client=client, tools={}, session_store=store)

        first = orchestrator.run(chat_id="chat-1", instructions="Be helpful.", user_message="First")
        second = orchestrator.run(chat_id="chat-1", instructions="Be helpful.", user_message="Second")

        self.assertEqual(first.session_id, second.session_id)
        self.assertEqual(client.requests[0].session_id, client.requests[1].session_id)

    def test_unknown_tool_is_rejected_before_handler_execution(self) -> None:
        client = ScriptedModelClient([
            ToolCallEvent("event-1", ToolCall("call-1", "unknown", {})),
        ])
        orchestrator = AgentOrchestrator(model_client=client, tools={})

        with self.assertRaises(ToolPermissionError):
            orchestrator.run(chat_id="chat-1", instructions="Use tools.", user_message="Do thing")

    def test_step_limit_stops_repeated_tool_requests(self) -> None:
        call = ToolCall("call-1", "tool", {})
        client = ScriptedModelClient([
            ToolCallEvent("event-1", call),
            ToolCallEvent("event-2", ToolCall("call-2", "tool", {})),
        ])
        orchestrator = AgentOrchestrator(model_client=client, tools={"tool": lambda _: {}}, max_tool_steps=1)

        with self.assertRaises(StepLimitExceeded):
            orchestrator.run(chat_id="chat-1", instructions="Use tools.", user_message="Repeat")

    def test_handler_failure_has_a_safe_structured_exception(self) -> None:
        client = ScriptedModelClient([
            ToolCallEvent("event-1", ToolCall("call-1", "broken", {})),
        ])
        orchestrator = AgentOrchestrator(
            model_client=client,
            tools={"broken": lambda _: (_ for _ in ()).throw(RuntimeError("private failure"))},
        )

        with self.assertRaises(ToolExecutionError) as context:
            orchestrator.run(chat_id="chat-1", instructions="Use tools.", user_message="Run")
        self.assertEqual(str(context.exception), "tool execution failed for broken")


if __name__ == "__main__":
    unittest.main()
