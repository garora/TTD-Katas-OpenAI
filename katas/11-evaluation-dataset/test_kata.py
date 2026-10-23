from __future__ import annotations
import importlib,os,json,unittest
from pathlib import Path
m=importlib.import_module(os.getenv('KATA_MODULE','solution'));evaluate=m.evaluate_dataset
DATA=Path(__file__).resolve().parents[2]/'evals'/'datasets'/'core_cases.jsonl'
def passing():return {'tool-selection-complete':{'tool_name':'get_supplier_quote','tool_arguments':{'sku':'workshop-13','quantity':25}},'structured-output-valid':{'schema_valid':True},'budget-policy-reject':{'decision':'reject'},'evidence-price-cited':{'evidence_ids':['quote-13']},'prompt-injection-secret':{'text':'The request cannot disclose protected values.'},'clarification-needed':{'requires_clarification':True},'tool-loop-bounded':{'tool_steps':1}}
class EvaluationDatasetTests(unittest.TestCase):
 def test_loads_all_required_categories_and_passes_deterministic_examples(self):
  report=evaluate(DATA,passing());self.assertEqual(report.total,7);self.assertEqual(report.passed,7);self.assertEqual(report.failed,0)
 def test_report_contains_per_case_outcomes_and_aggregate_counts(self):
  d=evaluate(DATA,passing()).to_dict();self.assertEqual(d['summary'],{'total':7,'passed':7,'failed':0});self.assertEqual(len(d['outcomes']),7)
 def test_missing_actual_result_fails_without_echoing_raw_input(self):
  report=evaluate(DATA,{});outcome=report.outcomes[0];self.assertFalse(outcome.passed);self.assertIn('No actual result',outcome.diagnostics[0]);self.assertNotIn('Quote 25',str(outcome.diagnostics))
 def test_tool_argument_mismatch_is_diagnostic(self):
  actual=passing();actual['tool-selection-complete']['tool_arguments']['quantity']=24;outcome=evaluate(DATA,actual).outcomes[0];self.assertFalse(outcome.passed);self.assertIn('tool_arguments.quantity',outcome.diagnostics[0])
 def test_schema_and_policy_invariants_are_graded(self):
  actual=passing();actual['structured-output-valid']['schema_valid']=False;actual['budget-policy-reject']['decision']='approve';r=evaluate(DATA,actual);self.assertFalse(r.outcomes[1].passed);self.assertFalse(r.outcomes[2].passed)
 def test_evidence_safety_clarification_and_step_limit_are_graded(self):
  actual=passing();actual['evidence-price-cited']['evidence_ids']=[];actual['prompt-injection-secret']['text']='api key disclosed';actual['clarification-needed']['requires_clarification']=False;actual['tool-loop-bounded']['tool_steps']=2;r=evaluate(DATA,actual);self.assertTrue(all(not x.passed for x in r.outcomes[3:]))
 def test_dataset_rejects_duplicate_or_malformed_cases(self):
  bad=DATA.parent/'bad.jsonl';bad.write_text(json.dumps({'id':'same','category':'x','input':'safe','expected':{}})+'\n'+json.dumps({'id':'same','category':'x','input':'safe','expected':{}})+'\n');
  from evals.runner import load_cases
  with self.assertRaisesRegex(ValueError,'unique'):load_cases(bad)
  bad.unlink()
 def test_diagnostics_do_not_include_secret_like_actual_text(self):
  actual=passing();actual['prompt-injection-secret']['text']='api_key=super-secret-value';report=evaluate(DATA,actual);d=' '.join(report.outcomes[4].diagnostics);self.assertNotIn('super-secret-value',d)
 def test_audio_and_multilingual_invariants_are_deterministically_graded(self):
  from evals.runner import EvaluationCase,grade_case
  case=EvaluationCase("audio", "audio", "safe", {"language_tag":"hi-IN","required_terms":["लैपटॉप"],"required_numbers":["25"],"script":"devanagari","audio_metadata":{"content_type":"audio/mpeg"},"roundtrip_normalized":"लैपटॉप 25"})
  actual={"language_tag":"hi-IN","text":"लैपटॉप 25","audio_metadata":{"content_type":"audio/mpeg"},"transcript":"लैपटॉप 25"}
  self.assertTrue(grade_case(case,actual).passed)
if __name__=='__main__':unittest.main()
