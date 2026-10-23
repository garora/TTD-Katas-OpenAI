import importlib,json,os,unittest
from pathlib import Path
m=importlib.import_module(os.getenv("KATA_MODULE","solution"));R=m.TTSRequest;V=m.validate_tts_fixture
O=json.loads((Path(__file__).resolve().parents[2]/"tests/fixtures/audio/tts_output.json").read_text())
class TTSTests(unittest.TestCase):
 def req(self,**k):
  values={"text":"Hello 25","voice":"alloy","locale":"en-US"};values.update(k);return R(**values)
 def test_validates_synthetic_output(self):self.assertEqual(V(self.req(),O).duration_ms,920)
 def test_output_keeps_voice_and_model(self):o=V(self.req(),O);self.assertEqual((o.voice,o.model),("alloy","gpt-4o-mini-tts"))
 def test_rejects_invalid_locale_speed_format_or_disclosure(self):
  for r in (self.req(locale="English"),self.req(speed=9),self.req(output_format="flac"),self.req(disclosure=False)):
   with self.subTest(r=r):
    with self.assertRaises(ValueError):V(r,O)
 def test_rejects_missing_or_invalid_metadata(self):
  for o in ({},{**O,"byte_length":0},{**O,"content_type":"text/plain"}):
   with self.subTest(o=o):
    with self.assertRaises(ValueError):V(self.req(),o)
 def test_rejects_voice_provenance_mismatch(self):
  with self.assertRaises(ValueError):V(self.req(),{**O,"voice":"nova"})
 def test_requires_non_blank_text_and_voice(self):
  for r in (R("","alloy","en"),R("hi","","en")):
   with self.assertRaises(ValueError):V(r,O)
if __name__=="__main__":unittest.main()
