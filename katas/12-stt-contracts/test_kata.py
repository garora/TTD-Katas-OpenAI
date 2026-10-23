import importlib,json,os,unittest
from pathlib import Path
m=importlib.import_module(os.getenv("KATA_MODULE","solution"));A=m.AudioInput;N=m.normalize_transcription
R=json.loads((Path(__file__).resolve().parents[2]/"tests/fixtures/audio/stt_response.json").read_text())
class STTTests(unittest.TestCase):
 def audio(self,**k): return A("fixture.mp3","audio/mpeg",1024,**k)
 def test_normalizes_fixture_transcript(self): self.assertEqual(N(self.audio(language_hint="en-US"),R).text,"quote 25 workshop laptops.")
 def test_preserves_segment_timing(self): self.assertEqual(N(self.audio(),R).segments[0].end_ms,1200)
 def test_rejects_invalid_language_hint(self):
  with self.assertRaises(ValueError):N(self.audio(language_hint="english"),R)
 def test_rejects_invalid_audio_metadata(self):
  for a in (A("fixture.txt","audio/mpeg",1),A("fixture.mp3","text/plain",1),A("fixture.mp3","audio/mpeg",0)):
   with self.subTest(a=a):
    with self.assertRaises(ValueError):N(a,R)
 def test_rejects_missing_or_bad_segments(self):
  for r in ({"text":"x","language":"en","segments":[]},{"text":"x","language":"en","segments":[{"start_ms":1,"end_ms":1,"text":"x"}]},):
   with self.subTest(r=r):
    with self.assertRaises(ValueError):N(self.audio(),r)
 def test_rejects_invalid_response_language(self):
  r=dict(R,language="English")
  with self.assertRaises(ValueError):N(self.audio(),r)
if __name__=="__main__":unittest.main()
