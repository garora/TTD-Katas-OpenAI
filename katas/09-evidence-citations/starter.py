"""Starter implementation for Kata 09: evidence and citation mapping."""
from __future__ import annotations
from collections.abc import Mapping,Sequence
from dataclasses import dataclass
from typing import Literal
@dataclass(frozen=True)
class EvidenceRecord: evidence_id:str; source:str; facts:Mapping[str,object]
@dataclass(frozen=True)
class Claim: field:str; value:object; evidence_id:str; source:str; kind:Literal['observed']='observed'
@dataclass(frozen=True)
class Uncertainty: field:str; code:Literal['missing_evidence','conflicting_evidence']; evidence_ids:tuple[str,...]=()
@dataclass(frozen=True)
class DerivedRecommendation: decision:str; evidence_ids:tuple[str,...]
@dataclass(frozen=True)
class GroundedResponse:
 claims:tuple[Claim,...]=(); uncertainties:tuple[Uncertainty,...]=(); recommendation:DerivedRecommendation|None=None
 def to_dict(self)->dict[str,object]: raise NotImplementedError("Implement one test at a time")
def assemble_grounded_response(evidence:Sequence[EvidenceRecord],requested_fields:Sequence[str],recommendation:DerivedRecommendation|None=None)->GroundedResponse:raise NotImplementedError("Implement one test at a time")
