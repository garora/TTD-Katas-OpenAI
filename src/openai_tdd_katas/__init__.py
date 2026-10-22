"""Reusable, offline-first building blocks for the OpenAI TDD kata curriculum."""

from .contracts import (
    AgentResult,
    ContractError,
    Decision,
    Evidence,
    PolicyDecision,
    ProcurementRequirements,
    SessionRecord,
    SupplierQuote,
    ToolCall,
    ToolResult,
)
from .model_client import ModelClient, ModelRequest, TerminalEvent, ToolCallEvent
from .orchestration import AgentOrchestrator, InMemorySessionStore, StepLimitExceeded, ToolExecutionError
from .policy import ToolPermissionError, ensure_tool_allowed, evaluate_quote
from .tools import CATALOG, ToolInputError, UnknownSkuError, get_supplier_quote

__all__ = [
    "AgentOrchestrator",
    "AgentResult",
    "CATALOG",
    "ContractError",
    "Decision",
    "ensure_tool_allowed",
    "Evidence",
    "evaluate_quote",
    "get_supplier_quote",
    "InMemorySessionStore",
    "ModelClient",
    "ModelRequest",
    "PolicyDecision",
    "ProcurementRequirements",
    "SessionRecord",
    "StepLimitExceeded",
    "SupplierQuote",
    "TerminalEvent",
    "ToolCall",
    "ToolCallEvent",
    "ToolExecutionError",
    "ToolInputError",
    "ToolPermissionError",
    "ToolResult",
    "UnknownSkuError",
]
