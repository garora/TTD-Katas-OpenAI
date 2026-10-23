from __future__ import annotations
from collections.abc import Callable,Mapping
from dataclasses import dataclass
from typing import Literal
@dataclass(frozen=True)
class DelegationTask: task_id:str;role:str;shared_facts:Mapping[str,object];context:str
@dataclass(frozen=True)
class DelegationResult: task_id:str;role:str;status:Literal['completed','failed','timed_out','deferred'];findings:Mapping[str,object]|None=None;uncertainty:str|None=None
@dataclass(frozen=True)
class DelegationSummary: status:Literal['ready','needs_follow_up'];quote_facts:Mapping[str,object];requirements:Mapping[str,object];tasks:tuple[DelegationTask,...];results:tuple[DelegationResult,...];uncertainties:tuple[str,...]
def delegate_procurement_review(quote_facts:Mapping[str,object],requirements:Mapping[str,object],delegates:Mapping[str,Callable[[DelegationTask],DelegationResult]],max_concurrency:int=2)->DelegationSummary:raise NotImplementedError('Implement one test at a time')
