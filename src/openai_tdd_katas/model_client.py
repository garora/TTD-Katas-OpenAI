"""Provider-neutral model-client protocol and normalized model events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .contracts import ContractError, ToolCall, ToolResult


@dataclass(frozen=True)
class ModelRequest:
    session_id: str
    instructions: str
    user_message: str

    def __post_init__(self) -> None:
        for field_name in ("session_id", "instructions", "user_message"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ContractError(f"{field_name} must be a non-blank string")
            object.__setattr__(self, field_name, value.strip())


@dataclass(frozen=True)
class TerminalEvent:
    """A provider-normalized event carrying the final assistant text."""

    event_id: str
    text: str

    def __post_init__(self) -> None:
        for field_name in ("event_id", "text"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ContractError(f"{field_name} must be a non-blank string")
            object.__setattr__(self, field_name, value.strip())


@dataclass(frozen=True)
class ToolCallEvent:
    """A provider-normalized event requesting an application tool call."""

    event_id: str
    tool_call: ToolCall

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ContractError("event_id must be a non-blank string")
        object.__setattr__(self, "event_id", self.event_id.strip())
        if not isinstance(self.tool_call, ToolCall):
            raise ContractError("tool_call must be a ToolCall")


ModelEvent = TerminalEvent | ToolCallEvent


class ModelClient(Protocol):
    """Minimal adapter interface used by deterministic orchestration tests."""

    def start_turn(self, request: ModelRequest) -> ModelEvent:
        """Start a model turn and return its next normalized event."""

    def continue_after_tool(self, session_id: str, tool_result: ToolResult) -> ModelEvent:
        """Resume a model turn after a local tool handler has completed."""
