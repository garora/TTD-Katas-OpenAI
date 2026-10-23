"""Starter implementation for Kata 05: Build a Safe Tool-Execution Loop."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal, Protocol


class ToolLoopClient(Protocol):
    def start_turn(self, user_message: str) -> "ModelEvent": ...
    def continue_after_tool(self, tool_result: "NormalizedToolResult") -> "ModelEvent": ...


@dataclass(frozen=True)
class TerminalEvent:
    text: str


@dataclass(frozen=True)
class ToolCallEvent:
    call_id: str
    name: str
    arguments: object


ModelEvent = TerminalEvent | ToolCallEvent
ToolHandler = object


@dataclass(frozen=True)
class NormalizedToolResult:
    call_id: str
    name: str
    output: Mapping[str, object]
    source: str


@dataclass(frozen=True)
class ToolLoopResult:
    status: Literal["completed", "failed"]
    final_text: str | None = None
    error_code: str | None = None
    tool_calls: tuple[ToolCallEvent, ...] = ()
    tool_results: tuple[NormalizedToolResult, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "final_text": self.final_text,
            "error_code": self.error_code,
            "tool_calls": [call.__dict__ for call in self.tool_calls],
            "tool_results": [
                {"call_id": result.call_id, "name": result.name, "output": dict(result.output), "source": result.source}
                for result in self.tool_results
            ],
        }


class ScriptedModelClient:
    """Synthetic event client for tests; it does not use a provider or network."""

    def __init__(self, events: list[ModelEvent]) -> None:
        self._events = list(events)
        self.started_messages: list[str] = []
        self.continued_results: list[NormalizedToolResult] = []

    def start_turn(self, user_message: str) -> ModelEvent:
        self.started_messages.append(user_message)
        return self._next_event()

    def continue_after_tool(self, tool_result: NormalizedToolResult) -> ModelEvent:
        self.continued_results.append(tool_result)
        return self._next_event()

    def _next_event(self) -> ModelEvent:
        return self._events.pop(0)


def run_tool_loop(
    user_message: str,
    *,
    model_client: ToolLoopClient,
    tools: Mapping[str, ToolHandler],
    max_tool_steps: int = 4,
) -> ToolLoopResult:
    """Process synthetic model events one bounded step at a time.

    TODO: implement the terminal path, validation/allow-list path, normalized
    result handoff, safe failure results, and configurable step limit.
    """
    raise NotImplementedError("Implement one test at a time")
