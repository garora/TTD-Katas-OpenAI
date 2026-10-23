"""Starter implementation for Kata 04: Tool Selection and Clarification."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, Protocol


class ToolSelectionClient(Protocol):
    def select_action(self, user_request: str) -> "ModelIntent": ...


@dataclass(frozen=True)
class ToolCallIntent:
    name: str
    arguments: Mapping[str, object]


@dataclass(frozen=True)
class ClarificationIntent:
    missing_fields: tuple[str, ...]


ModelIntent = ToolCallIntent | ClarificationIntent
ToolHandler = object


class RecordedModelClient:
    """A recorded fake that lets this kata run completely offline."""

    def __init__(self, events_by_request: Mapping[str, ModelIntent]) -> None:
        self._events_by_request = dict(events_by_request)
        self.requests: list[str] = []

    def select_action(self, user_request: str) -> ModelIntent:
        self.requests.append(user_request)
        return self._events_by_request[user_request]


@dataclass(frozen=True)
class ToolSelectionResult:
    status: Literal["tool_called", "clarification", "rejected"]
    tool_name: str | None = None
    arguments: Mapping[str, object] | None = None
    tool_result: Mapping[str, object] | None = None
    missing_fields: tuple[str, ...] = ()
    reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "tool_name": self.tool_name,
            "arguments": dict(self.arguments) if self.arguments is not None else None,
            "tool_result": dict(self.tool_result) if self.tool_result is not None else None,
            "missing_fields": list(self.missing_fields),
            "reason": self.reason,
        }


def run_tool_selection(
    user_request: str,
    *,
    model_client: ToolSelectionClient,
    tools: Mapping[str, ToolHandler],
) -> ToolSelectionResult:
    """Normalize one model intent before any deterministic tool execution.

    TODO: fetch the model intent, distinguish clarification from tool calls,
    validate a quote call against an allow-list/schema, then dispatch only a
    validated handler. Invalid requests should return `rejected`, not invoke a
    tool and not fabricate a quote.
    """
    raise NotImplementedError("Implement one test at a time")
