"""Bounded provider-neutral tool-loop and in-memory session orchestration."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, is_dataclass
from uuid import uuid4

from .contracts import AgentResult, SessionRecord, ToolCall, ToolResult
from .model_client import ModelClient, ModelEvent, ModelRequest, TerminalEvent, ToolCallEvent
from .policy import ensure_tool_allowed

ToolHandler = Callable[[Mapping[str, object]], object]


class OrchestrationError(RuntimeError):
    """Base class for predictable agent-loop errors."""


class StepLimitExceeded(OrchestrationError):
    """Raised when a model continues requesting tools past the configured limit."""


class ToolExecutionError(OrchestrationError):
    """Raised when a validated local tool handler fails or returns an invalid result."""


class InMemorySessionStore:
    """Small deterministic-friendly session repository for kata exercises."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionRecord] = {}

    def get_or_create(self, chat_id: str) -> SessionRecord:
        existing = self._sessions.get(chat_id)
        if existing:
            return existing
        session = SessionRecord(chat_id=chat_id, session_id=f"session-{uuid4()}")
        self._sessions[chat_id] = session
        return session


def _as_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        candidate = value.to_dict()
        if isinstance(candidate, Mapping):
            return dict(candidate)
    if is_dataclass(value):
        candidate = asdict(value)
        if isinstance(candidate, Mapping):
            return dict(candidate)
    raise ToolExecutionError("tool handler must return a mapping or serializable domain result")


class AgentOrchestrator:
    """Drive a bounded tool loop while retaining observable calls/results."""

    def __init__(
        self,
        *,
        model_client: ModelClient,
        tools: Mapping[str, ToolHandler],
        session_store: InMemorySessionStore | None = None,
        max_tool_steps: int = 4,
    ) -> None:
        if isinstance(max_tool_steps, bool) or not isinstance(max_tool_steps, int) or max_tool_steps <= 0:
            raise ValueError("max_tool_steps must be a positive integer")
        self._model_client = model_client
        self._tools = dict(tools)
        self._session_store = session_store or InMemorySessionStore()
        self._max_tool_steps = max_tool_steps

    def run(self, *, chat_id: str, instructions: str, user_message: str) -> AgentResult:
        session = self._session_store.get_or_create(chat_id)
        event: ModelEvent = self._model_client.start_turn(
            ModelRequest(
                session_id=session.session_id,
                instructions=instructions,
                user_message=user_message,
            )
        )
        calls: list[ToolCall] = []
        results: list[ToolResult] = []

        for _ in range(self._max_tool_steps + 1):
            if isinstance(event, TerminalEvent):
                return AgentResult(
                    session_id=session.session_id,
                    final_text=event.text,
                    tool_calls=tuple(calls),
                    tool_results=tuple(results),
                )
            if not isinstance(event, ToolCallEvent):
                raise OrchestrationError(f"unsupported model event: {type(event).__name__}")
            if len(calls) >= self._max_tool_steps:
                raise StepLimitExceeded(f"tool loop exceeded {self._max_tool_steps} steps")

            call = event.tool_call
            ensure_tool_allowed(call.name, self._tools.keys())
            try:
                output = _as_mapping(self._tools[call.name](call.arguments))
            except OrchestrationError:
                raise
            except Exception as error:
                raise ToolExecutionError(f"tool execution failed for {call.name}") from error

            result = ToolResult(
                call_id=call.call_id,
                name=call.name,
                output=output,
                source=str(output.get("source", call.name)),
            )
            calls.append(call)
            results.append(result)
            event = self._model_client.continue_after_tool(session.session_id, result)

        raise StepLimitExceeded(f"tool loop exceeded {self._max_tool_steps} steps")
