from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class RoundTripFixture: source_text:str; transcript:str; locale:str; duration_ms:int; latency_ms:int
@dataclass(frozen=True)
class RoundTripGrade: passed:bool; reasons:tuple[str,...]
def grade_round_trip(fixture:RoundTripFixture,required_terms:tuple[str,...],max_latency_ms:int)->RoundTripGrade:raise NotImplementedError("Implement one test at a time")
