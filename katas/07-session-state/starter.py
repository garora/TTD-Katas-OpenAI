"""Starter implementation for Kata 07: Session State and Turn Lifecycle."""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum

class TurnStatus(StrEnum):
    OPEN="open"; COMPLETED="completed"; FAILED="failed"

@dataclass(frozen=True)
class SessionRecord:
    chat_id:str; session_id:str

@dataclass(frozen=True)
class TurnContext:
    chat_id:str; session_id:str; turn_id:str; action_key:str; status:TurnStatus; should_execute:bool

class InMemorySessionStore:
    """TODO: implement deterministic session and turn lifecycle behavior."""
    def open_turn(self, chat_id:str, action_key:str)->TurnContext:
        raise NotImplementedError("Implement one test at a time")
    def complete_turn(self, turn_id:str)->TurnContext:
        raise NotImplementedError("Implement one test at a time")
    def fail_turn(self, turn_id:str)->TurnContext:
        raise NotImplementedError("Implement one test at a time")
    def expire_session(self, chat_id:str)->None:
        raise NotImplementedError("Implement one test at a time")
    def current_session(self, chat_id:str)->SessionRecord|None:
        raise NotImplementedError("Implement one test at a time")
    def get_turn(self, turn_id:str)->TurnContext:
        raise NotImplementedError("Implement one test at a time")
