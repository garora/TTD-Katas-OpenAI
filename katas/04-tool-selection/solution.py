"""Reference solution for Kata 04: Tool Selection and Clarification."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal, Protocol


class ToolSelectionClient(Protocol):
    """A narrow adapter. Tests use RecordedModelClient; no provider SDK is needed."""

    def select_action(self, user_request: str) -> "ModelIntent": ...


@dataclass(frozen=True)
class ToolCallIntent:
    name: str
    arguments: Mapping[str, object]


@dataclass(frozen=True)
class ClarificationIntent:
    missing_fields: tuple[str, ...]


ModelIntent = ToolCallIntent | ClarificationIntent
ToolHandler = Callable[[Mapping[str, object]], Mapping[str, object]]
_ALLOWED_TOOLS = frozenset({"get_supplier_quote"})
_REQUIRED_QUOTE_FIELDS = frozenset({"sku", "quantity"})


@dataclass(frozen=True)
class ToolSelectionResult:
    """A JSON-friendly observable result for one proposed model action."""

    status: Literal["tool_called", "clarification", "rejected"]
    tool_name: str | None = None
    arguments: Mapping[str, object] | None = None
    tool_result: Mapping[str, object] | None = None
    missing_fields: tuple[str, ...] = ()
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"tool_called", "clarification", "rejected"}:
            raise ValueError("status is not supported")
        if self.arguments is not None:
            object.__setattr__(self, "arguments", dict(self.arguments))
        if self.tool_result is not None:
            object.__setattr__(self, "tool_result", dict(self.tool_result))
        object.__setattr__(self, "missing_fields", tuple(self.missing_fields))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "tool_name": self.tool_name,
            "arguments": dict(self.arguments) if self.arguments is not None else None,
            "tool_result": dict(self.tool_result) if self.tool_result is not None else None,
            "missing_fields": list(self.missing_fields),
            "reason": self.reason,
        }


class RecordedModelClient:
    """Small recorded-event fake used by tests and offline kata exploration."""

    def __init__(self, events_by_request: Mapping[str, ModelIntent]) -> None:
        self._events_by_request = dict(events_by_request)
        self.requests: list[str] = []

    def select_action(self, user_request: str) -> ModelIntent:
        self.requests.append(user_request)
        try:
            return self._events_by_request[user_request]
        except KeyError as error:
            raise ValueError("No recorded model event for this request") from error


def _non_blank_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-blank string")
    return value.strip()


def _validate_quote_arguments(arguments: object) -> dict[str, object]:
    if not isinstance(arguments, Mapping):
        raise ValueError("tool arguments must be a mapping")
    if set(arguments) != _REQUIRED_QUOTE_FIELDS:
        raise ValueError("quote arguments must contain only sku and quantity")

    sku = _non_blank_text(arguments.get("sku"), "sku")
    quantity = arguments.get("quantity")
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise ValueError("quantity must be a positive integer")
    return {"sku": sku, "quantity": quantity}


def _clarification_result(intent: ClarificationIntent) -> ToolSelectionResult:
    fields = tuple(
        _non_blank_text(field, "missing field")
        for field in intent.missing_fields
    )
    if not fields:
        return ToolSelectionResult(status="rejected", reason="clarification must name missing fields")
    return ToolSelectionResult(status="clarification", missing_fields=fields)


def _rejected(reason: str, tool_name: str | None = None) -> ToolSelectionResult:
    return ToolSelectionResult(status="rejected", tool_name=tool_name, reason=reason)


def run_tool_selection(
    user_request: str,
    *,
    model_client: ToolSelectionClient,
    tools: Mapping[str, ToolHandler],
) -> ToolSelectionResult:
    """Validate a single proposed model action before deterministic dispatch."""
    _non_blank_text(user_request, "user_request")
    intent = model_client.select_action(user_request)

    if isinstance(intent, ClarificationIntent):
        return _clarification_result(intent)
    if not isinstance(intent, ToolCallIntent):
        return _rejected("model event is not a supported intent")

    try:
        tool_name = _non_blank_text(intent.name, "tool name")
    except ValueError as error:
        return _rejected(str(error))
    if tool_name not in _ALLOWED_TOOLS:
        return _rejected("tool is not authorized", tool_name)
    if tool_name not in tools:
        return _rejected("authorized tool is not registered", tool_name)

    try:
        arguments = _validate_quote_arguments(intent.arguments)
    except ValueError as error:
        return _rejected(str(error), tool_name)

    try:
        tool_result = tools[tool_name](arguments)
    except Exception:
        # Preserve an exception only in private logs. The normalized result never
        # returns handler internals or invented supplier data to the caller.
        return _rejected("validated tool handler failed", tool_name)
    if not isinstance(tool_result, Mapping):
        return _rejected("tool handler must return a mapping", tool_name)

    return ToolSelectionResult(
        status="tool_called",
        tool_name=tool_name,
        arguments=arguments,
        tool_result=tool_result,
    )
