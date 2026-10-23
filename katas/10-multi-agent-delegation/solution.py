"""Reference solution for Kata 10: bounded local delegation."""
from __future__ import annotations
from collections.abc import Callable,Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Literal
def _text(v:object,f:str)->str:
 if not isinstance(v,str) or not v.strip():raise ValueError(f'{f} must be a non-blank string')
 return v.strip()
def _mapping(v:object,f:str)->dict[str,object]:
 if not isinstance(v,Mapping):raise ValueError(f'{f} must be a mapping')
 return dict(v)
@dataclass(frozen=True)
class DelegationTask:
 task_id:str;role:str;shared_facts:Mapping[str,object];context:str
 def __post_init__(self):
  for f in ('task_id','role','context'):object.__setattr__(self,f,_text(getattr(self,f),f))
  object.__setattr__(self,'shared_facts',_mapping(self.shared_facts,'shared_facts'))
@dataclass(frozen=True)
class DelegationResult:
 task_id:str;role:str;status:Literal['completed','failed','timed_out','deferred'];findings:Mapping[str,object]|None=None;uncertainty:str|None=None
 def __post_init__(self):
  object.__setattr__(self,'task_id',_text(self.task_id,'task_id'));object.__setattr__(self,'role',_text(self.role,'role'))
  if self.status not in {'completed','failed','timed_out','deferred'}:raise ValueError('unsupported result status')
  if self.findings is not None:object.__setattr__(self,'findings',_mapping(self.findings,'findings'))
  if self.status=='completed' and self.findings is None:raise ValueError('completed result needs findings')
  if self.status!='completed':object.__setattr__(self,'uncertainty',_text(self.uncertainty or 'child did not complete','uncertainty'))
@dataclass(frozen=True)
class DelegationSummary:
 status:Literal['ready','needs_follow_up'];quote_facts:Mapping[str,object];requirements:Mapping[str,object];tasks:tuple[DelegationTask,...];results:tuple[DelegationResult,...];uncertainties:tuple[str,...]
 def to_dict(self)->dict[str,object]:return {'status':self.status,'quote_facts':dict(self.quote_facts),'requirements':dict(self.requirements),'tasks':[x.task_id for x in self.tasks],'results':[{'task_id':x.task_id,'role':x.role,'status':x.status,'findings':dict(x.findings) if x.findings else None,'uncertainty':x.uncertainty} for x in self.results],'uncertainties':list(self.uncertainties)}
def _tasks(quote:Mapping[str,object],requirements:Mapping[str,object])->tuple[DelegationTask,...]:
 shared={'quote_facts':dict(quote),'requirements':dict(requirements)}
 return (DelegationTask('budget-review','budget',shared,'Assess budget and delivery deadline.'),DelegationTask('technical-review','technical',shared,'Identify missing technical requirements.'))
def _execute(task:DelegationTask,delegates:Mapping[str,Callable[[DelegationTask],DelegationResult]])->DelegationResult:
 handler=delegates.get(task.role)
 if handler is None:return DelegationResult(task.task_id,task.role,'deferred',uncertainty='delegate is not registered')
 try:result=handler(task)
 except Exception:return DelegationResult(task.task_id,task.role,'failed',uncertainty='delegate failed')
 if not isinstance(result,DelegationResult) or result.task_id!=task.task_id or result.role!=task.role:return DelegationResult(task.task_id,task.role,'failed',uncertainty='delegate returned invalid correlation')
 return result
def delegate_procurement_review(quote_facts:Mapping[str,object],requirements:Mapping[str,object],delegates:Mapping[str,Callable[[DelegationTask],DelegationResult]],max_concurrency:int=2)->DelegationSummary:
 quote=_mapping(quote_facts,'quote_facts');requirements=_mapping(requirements,'requirements')
 if isinstance(max_concurrency,bool) or not isinstance(max_concurrency,int) or max_concurrency<=0:raise ValueError('max_concurrency must be a positive integer')
 tasks=_tasks(quote,requirements)
 with ThreadPoolExecutor(max_workers=min(max_concurrency,len(tasks))) as executor:results=tuple(executor.map(lambda task:_execute(task,delegates),tasks))
 uncertainties=tuple(result.uncertainty for result in results if result.status!='completed')
 return DelegationSummary('ready' if not uncertainties else 'needs_follow_up',quote,requirements,tasks,results,uncertainties)
