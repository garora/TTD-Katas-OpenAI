from __future__ import annotations
from dataclasses import dataclass
from evals.audio_grading import language_tag_is_valid,normalize_text
@dataclass(frozen=True)
class AudioInput: filename:str; content_type:str; byte_length:int; language_hint:str|None=None
@dataclass(frozen=True)
class Segment: start_ms:int; end_ms:int; text:str
@dataclass(frozen=True)
class Transcript: text:str; language:str; segments:tuple[Segment,...]
def _text(v,f):
 if not isinstance(v,str) or not v.strip():raise ValueError(f"{f} must be non-blank")
 return v.strip()
def _audio(audio):
 if not isinstance(audio,AudioInput):raise ValueError("audio must be AudioInput")
 if audio.content_type not in {"audio/mpeg","audio/wav","audio/webm"}:raise ValueError("unsupported content type")
 if not audio.filename.lower().endswith((".mp3",".wav",".webm")):raise ValueError("unsupported filename")
 if not isinstance(audio.byte_length,int) or audio.byte_length<=0:raise ValueError("byte_length must be positive")
 if audio.language_hint and not language_tag_is_valid(audio.language_hint):raise ValueError("invalid language hint")
def normalize_transcription(audio:AudioInput,response:dict)->Transcript:
 _audio(audio)
 if not isinstance(response,dict):raise ValueError("response must be a mapping")
 text=_text(response.get("text"),"text"); language=_text(response.get("language"),"language")
 if not language_tag_is_valid(language):raise ValueError("invalid response language")
 segments=[]
 for item in response.get("segments",[]):
  if not isinstance(item,dict):raise ValueError("segment must be a mapping")
  start,end=item.get("start_ms"),item.get("end_ms")
  if not isinstance(start,int) or not isinstance(end,int) or start<0 or end<=start:raise ValueError("invalid segment timing")
  segments.append(Segment(start,end,_text(item.get("text"),"segment text")))
 if not segments:raise ValueError("at least one segment is required")
 return Transcript(normalize_text(text),language,tuple(segments))
