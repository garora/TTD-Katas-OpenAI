"""Starter implementation for Kata 08: trusted and untrusted content boundaries."""
from __future__ import annotations
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class UntrustedReference: source:str; content:str
@dataclass(frozen=True)
class ContextEnvelope:
 policy_text:str; allowed_tools:frozenset[str]; reference:UntrustedReference
 def render_for_model(self)->str: raise NotImplementedError("Implement one test at a time")
@dataclass(frozen=True)
class DispatchResult:
 status:Literal['dispatched','rejected','tool_failed']; tool_name:str; output:Mapping[str,object]|None=None; reason:str|None=None

def build_context(policy_text:str,allowed_tools:set[str]|frozenset[str],reference:UntrustedReference)->ContextEnvelope: raise NotImplementedError("Implement one test at a time")
def extract_integer_facts(reference:UntrustedReference, fields:set[str])->dict[str,int]: raise NotImplementedError("Implement one test at a time")
def dispatch_tool(tool_name:str,arguments:object,context:ContextEnvelope,handlers:Mapping[str,Callable[[Mapping[str,object]],Mapping[str,object]]])->DispatchResult: raise NotImplementedError("Implement one test at a time")
