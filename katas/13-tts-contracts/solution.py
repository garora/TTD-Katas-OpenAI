from __future__ import annotations
from dataclasses import dataclass
from evals.audio_grading import language_tag_is_valid
@dataclass(frozen=True)
class TTSRequest: text:str; voice:str; locale:str; speed:float=1.0; output_format:str="mp3"; disclosure:bool=True
@dataclass(frozen=True)
class AudioOutput: content_type:str; byte_length:int; duration_ms:int; voice:str; model:str; source:str
def _text(v,f):
 if not isinstance(v,str) or not v.strip():raise ValueError(f"{f} must be non-blank")
 return v.strip()
def _request(r):
 if not isinstance(r,TTSRequest):raise ValueError("request must be TTSRequest")
 _text(r.text,"text");_text(r.voice,"voice")
 if not language_tag_is_valid(r.locale):raise ValueError("invalid locale")
 if not isinstance(r.speed,(int,float)) or isinstance(r.speed,bool) or not .25<=r.speed<=4:raise ValueError("speed must be between .25 and 4")
 if r.output_format not in {"mp3","wav","opus"}:raise ValueError("unsupported output format")
 if r.disclosure is not True:raise ValueError("disclosure is required")
def validate_tts_fixture(request:TTSRequest,output:dict)->AudioOutput:
 _request(request)
 if not isinstance(output,dict):raise ValueError("output must be a mapping")
 required=("content_type","byte_length","duration_ms","voice","model","source")
 if any(k not in output for k in required):raise ValueError("incomplete output metadata")
 if output["content_type"] not in {"audio/mpeg","audio/wav","audio/ogg"}:raise ValueError("unsupported content type")
 if not isinstance(output["byte_length"],int) or output["byte_length"]<=0 or not isinstance(output["duration_ms"],int) or output["duration_ms"]<=0:raise ValueError("invalid audio metadata")
 if output["voice"]!=request.voice:raise ValueError("voice provenance mismatch")
 return AudioOutput(*[output[k] for k in required])
