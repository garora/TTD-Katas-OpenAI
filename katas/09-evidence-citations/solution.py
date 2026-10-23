"""Reference solution for Kata 09: deterministic evidence-to-claim mapping."""
from __future__ import annotations
from collections.abc import Mapping,Sequence
from dataclasses import dataclass
from typing import Literal
def _text(value:object,field:str)->str:
 if not isinstance(value,str) or not value.strip():raise ValueError(f"{field} must be a non-blank string")
 return value.strip()
@dataclass(frozen=True)
class EvidenceRecord:
 evidence_id:str; source:str; facts:Mapping[str,object]
 def __post_init__(self):
  object.__setattr__(self,'evidence_id',_text(self.evidence_id,'evidence_id'));object.__setattr__(self,'source',_text(self.source,'source'))
  if not isinstance(self.facts,Mapping):raise ValueError('facts must be a mapping')
  object.__setattr__(self,'facts',dict(self.facts))
@dataclass(frozen=True)
class Claim:
 field:str;value:object;evidence_id:str;source:str;kind:Literal['observed']='observed'
 def __post_init__(self):
  for f in ('field','evidence_id','source'):object.__setattr__(self,f,_text(getattr(self,f),f))
  if self.kind!='observed':raise ValueError('claim kind must be observed')
@dataclass(frozen=True)
class Uncertainty:
 field:str;code:Literal['missing_evidence','conflicting_evidence'];evidence_ids:tuple[str,...]=()
 def __post_init__(self):
  object.__setattr__(self,'field',_text(self.field,'field'))
  if self.code not in {'missing_evidence','conflicting_evidence'}:raise ValueError('unsupported uncertainty code')
  object.__setattr__(self,'evidence_ids',tuple(_text(x,'evidence_id') for x in self.evidence_ids))
@dataclass(frozen=True)
class DerivedRecommendation:
 decision:str;evidence_ids:tuple[str,...]
 def __post_init__(self):object.__setattr__(self,'decision',_text(self.decision,'decision'));object.__setattr__(self,'evidence_ids',tuple(_text(x,'evidence_id') for x in self.evidence_ids))
@dataclass(frozen=True)
class GroundedResponse:
 claims:tuple[Claim,...]=();uncertainties:tuple[Uncertainty,...]=();recommendation:DerivedRecommendation|None=None
 def to_dict(self)->dict[str,object]:
  return {'claims':[{'field':x.field,'value':x.value,'evidence_id':x.evidence_id,'source':x.source,'kind':x.kind} for x in self.claims], 'uncertainties':[{'field':x.field,'code':x.code,'evidence_ids':list(x.evidence_ids)} for x in self.uncertainties], 'recommendation':None if self.recommendation is None else {'decision':self.recommendation.decision,'evidence_ids':list(self.recommendation.evidence_ids)}}
def assemble_grounded_response(evidence:Sequence[EvidenceRecord],requested_fields:Sequence[str],recommendation:DerivedRecommendation|None=None)->GroundedResponse:
 records=tuple(evidence)
 if not all(isinstance(x,EvidenceRecord) for x in records):raise ValueError('evidence must contain EvidenceRecord values')
 if len({x.evidence_id for x in records})!=len(records):raise ValueError('evidence IDs must be unique')
 fields=tuple(_text(x,'requested field') for x in requested_fields)
 claims=[];uncertainties=[]
 for field in fields:
  matches=[record for record in records if field in record.facts]
  values={repr(record.facts[field]) for record in matches}
  if not matches:uncertainties.append(Uncertainty(field,'missing_evidence'));continue
  if len(values)>1:uncertainties.append(Uncertainty(field,'conflicting_evidence',tuple(record.evidence_id for record in matches)));continue
  record=matches[0];claims.append(Claim(field,record.facts[field],record.evidence_id,record.source))
 if recommendation is not None:
  if not isinstance(recommendation,DerivedRecommendation):raise ValueError('recommendation must be a DerivedRecommendation')
  known={x.evidence_id for x in records}
  if not set(recommendation.evidence_ids).issubset(known):raise ValueError('recommendation references unknown evidence')
 return GroundedResponse(tuple(claims),tuple(uncertainties),recommendation)
