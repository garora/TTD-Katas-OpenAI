import importlib,json,os,unittest
from pathlib import Path
m=importlib.import_module(os.getenv("KATA_MODULE","solution"));F=m.RoundTripFixture;G=m.grade_round_trip
D=json.loads((Path(__file__).resolve().parents[2]/"tests/fixtures/audio/round_trip.json").read_text())
class RoundTripTests(unittest.TestCase):
 def fixture(self,**k):
  values={"source_text":D["source_text"],"transcript":D["transcript"],"locale":D["locale"],"duration_ms":D["duration_ms"],"latency_ms":D["latency_ms"]};values.update(k);return F(**values)
 def test_grades_normalized_matching_round_trip(self):self.assertTrue(G(self.fixture(),("workshop",),300).passed)
 def test_allows_case_and_spacing_variation(self):self.assertTrue(G(F("Quote 25"," quote   25 ","en-US",1,1),(),2).passed)
 def test_requires_terms_and_source_numbers(self):g=G(self.fixture(transcript="quote workshop laptops"),("workshop",),300);self.assertIn("missing number: 25",g.reasons)
 def test_rejects_missing_required_term(self):self.assertIn("missing term: catalog",G(self.fixture(),("catalog",),300).reasons)
 def test_grades_latency_separately(self):self.assertIn("latency budget exceeded",G(self.fixture(),(),100).reasons)
 def test_rejects_invalid_fixture_and_timing(self):
  with self.assertRaises(ValueError):G(F("x","y","English",1,1),(),1)
  with self.assertRaises(ValueError):G(self.fixture(),(),-1)
if __name__=="__main__":unittest.main()
