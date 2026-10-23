"""Offline contract tests for Kata 05's reference tool loop."""

from __future__ import annotations

import importlib
import os
import unittest


module = importlib.import_module(os.getenv("KATA_MODULE", "solution"))
NormalizedToolResult = module.NormalizedToolResult
ScriptedModelClient = module.ScriptedModelClient
TerminalEvent = module.TerminalEvent
ToolCallEvent = module.ToolCallEvent
ToolLoopResult = module.ToolLoopResult
run_tool_loop = module.run_tool_loop


class RecordingTool:
    def __init__(self, output: dict[str, object] | None = None) -> None:
        self.calls: list[dict[str, object]] = []
        self.output = output or {"value": "ok", "source": "local fixture"}

    def __call__(self, arguments: dict[str, object]) -> dict[str, object]:
        self.calls.append(dict(arguments))
        return dict(self.output)


def loop(events, tools=None, max_tool_steps=4):
    client = ScriptedModelClient(events)
    tool = RecordingTool()
    result = run_tool_loop(
        "Use the approved tool when needed.",
        model_client=client,
        tools=tools if tools is not None else {"lookup": tool},
        max_tool_steps=max_tool_steps,
    )
    return result, tool, client


class ToolLoopTests(unittest.TestCase):
    def test_terminal_event_completes_without_tool_dispatch(self) -> None:
        result, tool, client = loop([TerminalEvent("No tool is needed.")])

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.final_text, "No tool is needed.")
        self.assertEqual(result.tool_calls, ())
        self.assertEqual(result.tool_results, ())
        self.assertEqual(tool.calls, [])
        self.assertEqual(client.started_messages, ["Use the approved tool when needed."])

    def test_single_valid_tool_call_is_dispatched_and_normalized_before_continue(self) -> None:
        result, tool, client = loop([
            ToolCallEvent("call-1", "lookup", {"sku": "workshop-13"}),
            TerminalEvent("Quote retrieved."),
        ])

        self.assertEqual(result.status, "completed")
        self.assertEqual(tool.calls, [{"sku": "workshop-13"}])
        self.assertEqual(result.tool_calls[0].call_id, "call-1")
        self.assertEqual(result.tool_results[0].source, "local fixture")
        self.assertEqual(client.continued_results, [result.tool_results[0]])

    def test_multiple_sequential_calls_preserve_order_before_terminal_response(self) -> None:
        result, tool, client = loop([
            ToolCallEvent("call-1", "lookup", {"sku": "one"}),
            ToolCallEvent("call-2", "lookup", {"sku": "two"}),
            TerminalEvent("Both quotes retrieved."),
        ])

        self.assertEqual(result.status, "completed")
        self.assertEqual([call.call_id for call in result.tool_calls], ["call-1", "call-2"])
        self.assertEqual(tool.calls, [{"sku": "one"}, {"sku": "two"}])
        self.assertEqual([result.call_id for result in client.continued_results], ["call-1", "call-2"])

    def test_unknown_tool_fails_before_any_handler_runs(self) -> None:
        result, tool, client = loop([ToolCallEvent("call-1", "unknown", {})])

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error_code, "tool_not_authorized")
        self.assertEqual(result.tool_calls, ())
        self.assertEqual(tool.calls, [])
        self.assertEqual(client.continued_results, [])

    def test_non_mapping_arguments_fail_before_handler_runs(self) -> None:
        result, tool, client = loop([ToolCallEvent("call-1", "lookup", ["not", "a", "mapping"])])

        self.assertEqual(result.error_code, "invalid_tool_call")
        self.assertEqual(tool.calls, [])
        self.assertEqual(client.continued_results, [])

    def test_blank_call_id_or_tool_name_fails_before_handler_runs(self) -> None:
        for event in (ToolCallEvent("", "lookup", {}), ToolCallEvent("call-1", "  ", {})):
            with self.subTest(event=event):
                result, tool, _ = loop([event])
                self.assertEqual(result.error_code, "invalid_tool_call")
                self.assertEqual(tool.calls, [])

    def test_handler_exception_returns_structured_failure_without_private_details(self) -> None:
        def broken(arguments):
            raise RuntimeError("private catalog exception")

        result, _, client = loop([ToolCallEvent("call-1", "lookup", {})], {"lookup": broken})

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error_code, "tool_handler_failed")
        self.assertEqual(len(result.tool_calls), 1)
        self.assertEqual(result.tool_results, ())
        self.assertEqual(client.continued_results, [])
        self.assertNotIn("private catalog exception", str(result.to_dict()))

    def test_non_mapping_handler_output_returns_structured_failure(self) -> None:
        result, _, client = loop([ToolCallEvent("call-1", "lookup", {})], {"lookup": lambda arguments: ["bad"]})

        self.assertEqual(result.error_code, "tool_handler_failed")
        self.assertEqual(client.continued_results, [])

    def test_step_limit_stops_before_excess_handler_dispatch(self) -> None:
        result, tool, client = loop([
            ToolCallEvent("call-1", "lookup", {"n": 1}),
            ToolCallEvent("call-2", "lookup", {"n": 2}),
        ], max_tool_steps=1)

        self.assertEqual(result.error_code, "step_limit_exceeded")
        self.assertEqual(tool.calls, [{"n": 1}])
        self.assertEqual([result.call_id for result in client.continued_results], ["call-1"])
        self.assertEqual([call.call_id for call in result.tool_calls], ["call-1"])

    def test_max_tool_steps_must_be_a_positive_non_boolean_integer(self) -> None:
        for invalid_limit in (0, -1, True, "4"):
            with self.subTest(invalid_limit=invalid_limit):
                with self.assertRaisesRegex(ValueError, "max_tool_steps"):
                    run_tool_loop(
                        "message",
                        model_client=ScriptedModelClient([TerminalEvent("done")]),
                        tools={},
                        max_tool_steps=invalid_limit,
                    )

    def test_result_shape_is_json_friendly_and_preserves_completed_history(self) -> None:
        result, _, _ = loop([
            ToolCallEvent("call-1", "lookup", {"sku": "one"}),
            ToolCallEvent("call-2", "lookup", {"sku": "two"}),
        ], max_tool_steps=1)

        self.assertEqual(
            result.to_dict(),
            {
                "status": "failed",
                "final_text": None,
                "error_code": "step_limit_exceeded",
                "tool_calls": [{"call_id": "call-1", "name": "lookup", "arguments": {"sku": "one"}}],
                "tool_results": [{"call_id": "call-1", "name": "lookup", "output": {"value": "ok", "source": "local fixture"}, "source": "local fixture"}],
            },
        )


if __name__ == "__main__":
    unittest.main()
