from __future__ import annotations
from dataclasses import dataclass
from evals.audio_grading import language_tag_is_valid,normalize_text,numbers_in_text
@dataclass(frozen=True)
class RoundTripFixture: source_text:str; transcript:str; locale:str; duration_ms:int; latency_ms:int
@dataclass(frozen=True)
class RoundTripGrade: passed:bool; reasons:tuple[str,...]
def grade_round_trip(fixture:RoundTripFixture,required_terms:tuple[str,...],max_latency_ms:int)->RoundTripGrade:
 if not isinstance(fixture,RoundTripFixture):raise ValueError("fixture must be RoundTripFixture")
 if not fixture.source_text.strip() or not fixture.transcript.strip() or not language_tag_is_valid(fixture.locale):raise ValueError("invalid fixture text or locale")
 if not all(isinstance(x,int) and x>=0 for x in (fixture.duration_ms,fixture.latency_ms,max_latency_ms)):raise ValueError("invalid timing")
 source,transcript=normalize_text(fixture.source_text),normalize_text(fixture.transcript);reasons=[]
 for term in required_terms:
  if normalize_text(term) not in transcript:reasons.append(f"missing term: {term}")
 for number in numbers_in_text(source):
  if number not in numbers_in_text(transcript):reasons.append(f"missing number: {number}")
 if fixture.latency_ms>max_latency_ms:reasons.append("latency budget exceeded")
 return RoundTripGrade(not reasons,tuple(reasons))
