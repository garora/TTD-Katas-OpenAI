from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class TTSRequest: text:str; voice:str; locale:str; speed:float=1.0; output_format:str="mp3"; disclosure:bool=True
@dataclass(frozen=True)
class AudioOutput: content_type:str; byte_length:int; duration_ms:int; voice:str; model:str; source:str
def validate_tts_fixture(request:TTSRequest,output:dict)->AudioOutput:raise NotImplementedError("Implement one test at a time")
