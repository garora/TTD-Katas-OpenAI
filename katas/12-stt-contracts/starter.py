from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class AudioInput: filename:str; content_type:str; byte_length:int; language_hint:str|None=None
@dataclass(frozen=True)
class Segment: start_ms:int; end_ms:int; text:str
@dataclass(frozen=True)
class Transcript: text:str; language:str; segments:tuple[Segment,...]
def normalize_transcription(audio:AudioInput,response:dict)->Transcript: raise NotImplementedError("Implement one test at a time")
