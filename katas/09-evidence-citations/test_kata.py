from __future__ import annotations
import importlib,os,json,unittest
from pathlib import Path
m=importlib.import_module(os.getenv('KATA_MODULE','solution')); EvidenceRecord=m.EvidenceRecord;DerivedRecommendation=m.DerivedRecommendation;assemble_grounded_response=m.assemble_grounded_response
fixture=json.loads((Path(__file__).resolve().parents[2]/'tests'/'fixtures'/'tool-results'/'quote-13.json').read_text())
class EvidenceCitationTests(unittest.TestCase):
 def quote(self):return EvidenceRecord('quote-13','supplier catalog',fixture)
 def test_price_and_lead_time_claims_are_cited_to_quote_record(self):
  r=assemble_grounded_response([self.quote()],('total_usd','lead_days'));self.assertEqual([(x.field,x.value,x.evidence_id,x.source) for x in r.claims],[('total_usd',27475,'quote-13','supplier catalog'),('lead_days',7,'quote-13','supplier catalog')])
 def test_unsupported_field_becomes_missing_evidence_not_claim(self):
  r=assemble_grounded_response([self.quote()],('memory_gb',));self.assertEqual(r.claims,());self.assertEqual(r.uncertainties[0].code,'missing_evidence')
 def test_conflicting_sources_produce_uncertainty_not_silent_winner(self):
  a=self.quote();b=EvidenceRecord('quote-conflict','supplier catalog backup',{'total_usd':28000});r=assemble_grounded_response([a,b],('total_usd',));self.assertEqual(r.claims,());self.assertEqual(r.uncertainties[0].code,'conflicting_evidence');self.assertEqual(r.uncertainties[0].evidence_ids,('quote-13','quote-conflict'))
 def test_same_value_across_sources_is_still_grounded(self):
  b=EvidenceRecord('quote-copy','backup',{'lead_days':7});r=assemble_grounded_response([self.quote(),b],('lead_days',));self.assertEqual(r.claims[0].evidence_id,'quote-13')
 def test_recommendation_is_derived_and_separate_from_observed_claims(self):
  r=assemble_grounded_response([self.quote()],('total_usd',),DerivedRecommendation('approve',('quote-13',)));self.assertEqual(r.recommendation.decision,'approve');self.assertEqual(r.claims[0].kind,'observed')
 def test_recommendation_cannot_reference_unknown_evidence(self):
  with self.assertRaisesRegex(ValueError,'unknown evidence'):assemble_grounded_response([self.quote()],(),DerivedRecommendation('approve',('missing',)))
 def test_evidence_ids_must_be_unique(self):
  with self.assertRaisesRegex(ValueError,'unique'):assemble_grounded_response([self.quote(),self.quote()],())
 def test_invalid_evidence_and_field_inputs_are_rejected(self):
  with self.assertRaises(ValueError):assemble_grounded_response(['bad'],())
  with self.assertRaises(ValueError):assemble_grounded_response([self.quote()],(' ',))
 def test_response_serialization_is_machine_readable_without_model_prose(self):
  r=assemble_grounded_response([self.quote()],('total_usd','memory_gb'),DerivedRecommendation('approve',('quote-13',)));data=r.to_dict();self.assertEqual(data['claims'][0]['evidence_id'],'quote-13');self.assertEqual(data['uncertainties'][0]['code'],'missing_evidence');self.assertNotIn('explanation',data)
 def test_fact_type_is_preserved_for_ui_or_activity_rendering(self):
  r=assemble_grounded_response([self.quote()],('total_usd',));self.assertIsInstance(r.claims[0].value,int)
if __name__=='__main__':unittest.main()
