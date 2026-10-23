"""Reference solution for Kata 05: Build a Safe Tool-Execution Loop."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
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
ToolHandler = Callable[[Mapping[str, object]], Mapping[str, object]]


@dataclass(frozen=True)
class NormalizedToolResult:
    call_id: str
    name: str
    output: Mapping[str, object]
    source: str

    def __post_init__(self) -> None:
        for field in ("call_id", "name", "source"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-blank string")
            object.__setattr__(self, field, value.strip())
        if not isinstance(self.output, Mapping):
            raise ValueError("output must be a mapping")
        object.__setattr__(self, "output", dict(self.output))


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
            "tool_calls": [
                {"call_id": call.call_id, "name": call.name, "arguments": dict(call.arguments) if isinstance(call.arguments, Mapping) else None}
                for call in self.tool_calls
            ],
            "tool_results": [
                {"call_id": result.call_id, "name": result.name, "output": dict(result.output), "source": result.source}
                for result in self.tool_results
            ],
        }


class ScriptedModelClient:
    """Synthetic event source used by this offline kata and its tests."""

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
        if not self._events:
            raise ValueError("scripted model has no next event")
        return self._events.pop(0)


def _non_blank_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-blank string")
    return value.strip()


def _validated_call(event: ToolCallEvent, tools: Mapping[str, ToolHandler]) -> tuple[str, str, dict[str, object]]:
    call_id = _non_blank_text(event.call_id, "call_id")
    name = _non_blank_text(event.name, "tool name")
    if name not in tools:
        raise PermissionError("tool is not authorized")
    if not isinstance(event.arguments, Mapping):
        raise ValueError("tool arguments must be a mapping")
    return call_id, name, {key: value for key, value in event.arguments.items()}


def _normalized_output(call_id: str, name: str, output: object) -> NormalizedToolResult:
    if not isinstance(output, Mapping):
        raise ValueError("tool handler must return a mapping")
    source = output.get("source", name)
    if not isinstance(source, str) or not source.strip():
        source = name
    return NormalizedToolResult(call_id=call_id, name=name, output=output, source=source)


def _failed(
    error_code: str,
    calls: list[ToolCallEvent],
    results: list[NormalizedToolResult],
) -> ToolLoopResult:
    return ToolLoopResult(
        status="failed",
        error_code=error_code,
        tool_calls=tuple(calls),
        tool_results=tuple(results),
    )


def run_tool_loop(
    user_message: str,
    *,
    model_client: ToolLoopClient,
    tools: Mapping[str, ToolHandler],
    max_tool_steps: int = 4,
) -> ToolLoopResult:
    """Run a bounded, validated sequence of model events and local tools."""
    _non_blank_text(user_message, "user_message")
    if isinstance(max_tool_steps, bool) or not isinstance(max_tool_steps, int) or max_tool_steps <= 0:
        raise ValueError("max_tool_steps must be a positive integer")

    calls: list[ToolCallEvent] = []
    results: list[NormalizedToolResult] = []
    try:
        event: ModelEvent = model_client.start_turn(user_message)
    except Exception:
        return _failed("model_client_failed", calls, results)

    while True:
        if isinstance(event, TerminalEvent):
            try:
                text = _non_blank_text(event.text, "terminal text")
            except ValueError:
                return _failed("invalid_terminal_event", calls, results)
            return ToolLoopResult(
                status="completed",
                final_text=text,
                tool_calls=tuple(calls),
                tool_results=tuple(results),
            )

        if not isinstance(event, ToolCallEvent):
            return _failed("unsupported_model_event", calls, results)
        if len(calls) >= max_tool_steps:
            return _failed("step_limit_exceeded", calls, results)

        try:
            call_id, name, arguments = _validated_call(event, tools)
        except PermissionError:
            return _failed("tool_not_authorized", calls, results)
        except ValueError:
            return _failed("invalid_tool_call", calls, results)

        calls.append(event)
        try:
            output = tools[name](arguments)
            normalized = _normalized_output(call_id, name, output)
        except Exception:
            return _failed("tool_handler_failed", calls, results)

        results.append(normalized)
        try:
            event = model_client.continue_after_tool(normalized)
        except Exception:
            return _failed("model_client_failed", calls, results)
