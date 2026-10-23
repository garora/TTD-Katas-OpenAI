"""Reference solution for Kata 07: explicit in-memory session state."""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum

class TurnStatus(StrEnum):
    OPEN="open"; COMPLETED="completed"; FAILED="failed"

def _text(value:object, field:str)->str:
    if not isinstance(value,str) or not value.strip(): raise ValueError(f"{field} must be a non-blank string")
    return value.strip()

@dataclass(frozen=True)
class SessionRecord:
    chat_id:str; session_id:str
    def __post_init__(self):
        object.__setattr__(self,"chat_id",_text(self.chat_id,"chat_id")); object.__setattr__(self,"session_id",_text(self.session_id,"session_id"))

@dataclass(frozen=True)
class TurnContext:
    chat_id:str; session_id:str; turn_id:str; action_key:str; status:TurnStatus; should_execute:bool
    def __post_init__(self):
        for field in ("chat_id","session_id","turn_id","action_key"): object.__setattr__(self,field,_text(getattr(self,field),field))
        if not isinstance(self.status,TurnStatus): raise ValueError("status must be a TurnStatus")

class InMemorySessionStore:
    def __init__(self):
        self._sessions:dict[str,SessionRecord]={}; self._turns:dict[str,TurnContext]={}; self._completed:dict[tuple[str,str],str]={}; self._session_number=0; self._turn_number=0
    def _session_for(self,chat_id:str)->SessionRecord:
        session=self._sessions.get(chat_id)
        if session:return session
        self._session_number+=1; session=SessionRecord(chat_id,f"session-{self._session_number:04d}"); self._sessions[chat_id]=session; return session
    def open_turn(self,chat_id:str,action_key:str)->TurnContext:
        chat_id=_text(chat_id,"chat_id"); action_key=_text(action_key,"action_key"); session=self._session_for(chat_id); completed=self._completed.get((session.session_id,action_key))
        if completed:
            prior=self._turns[completed]
            return TurnContext(chat_id,session.session_id,prior.turn_id,action_key,TurnStatus.COMPLETED,False)
        self._turn_number+=1; turn=TurnContext(chat_id,session.session_id,f"turn-{self._turn_number:04d}",action_key,TurnStatus.OPEN,True); self._turns[turn.turn_id]=turn; return turn
    def _transition(self,turn_id:str,status:TurnStatus)->TurnContext:
        turn=self.get_turn(turn_id)
        if turn.status is not TurnStatus.OPEN: raise ValueError("turn is not open")
        updated=TurnContext(turn.chat_id,turn.session_id,turn.turn_id,turn.action_key,status,False); self._turns[turn_id]=updated
        if status is TurnStatus.COMPLETED:self._completed[(turn.session_id,turn.action_key)]=turn_id
        return updated
    def complete_turn(self,turn_id:str)->TurnContext:return self._transition(_text(turn_id,"turn_id"),TurnStatus.COMPLETED)
    def fail_turn(self,turn_id:str)->TurnContext:return self._transition(_text(turn_id,"turn_id"),TurnStatus.FAILED)
    def expire_session(self,chat_id:str)->None:self._sessions.pop(_text(chat_id,"chat_id"),None)
    def current_session(self,chat_id:str)->SessionRecord|None:return self._sessions.get(_text(chat_id,"chat_id"))
    def get_turn(self,turn_id:str)->TurnContext:
        try:return self._turns[_text(turn_id,"turn_id")]
        except KeyError as error:raise ValueError("unknown turn") from error
