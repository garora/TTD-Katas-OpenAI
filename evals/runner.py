"""Versioned, deterministic offline evaluation loader and graders."""
from __future__ import annotations
import json
from collections.abc import Mapping,Sequence
from dataclasses import dataclass
from pathlib import Path
@dataclass(frozen=True)
class EvaluationCase: case_id:str;category:str;input_text:str;expected:Mapping[str,object]
@dataclass(frozen=True)
class EvaluationOutcome: case_id:str;category:str;passed:bool;diagnostics:tuple[str,...]=()
@dataclass(frozen=True)
class EvaluationReport:
 outcomes:tuple[EvaluationOutcome,...]
 @property
 def total(self):return len(self.outcomes)
 @property
 def passed(self):return sum(x.passed for x in self.outcomes)
 @property
 def failed(self):return self.total-self.passed
 def to_dict(self):return {'summary':{'total':self.total,'passed':self.passed,'failed':self.failed},'outcomes':[{'case_id':x.case_id,'category':x.category,'passed':x.passed,'diagnostics':list(x.diagnostics)} for x in self.outcomes]}
def _text(v,f):
 if not isinstance(v,str) or not v.strip():raise ValueError(f'{f} must be a non-blank string')
 return v.strip()
def load_cases(path:Path)->tuple[EvaluationCase,...]:
 cases=[];seen=set()
 for line_no,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
  if not line.strip():continue
  try:data=json.loads(line)
  except json.JSONDecodeError as e:raise ValueError(f'invalid JSONL at line {line_no}') from e
  if not isinstance(data,Mapping):raise ValueError('case must be an object')
  case=EvaluationCase(_text(data.get('id'),'id'),_text(data.get('category'),'category'),_text(data.get('input'),'input'),data.get('expected'))
  if not isinstance(case.expected,Mapping):raise ValueError('expected must be a mapping')
  if case.case_id in seen:raise ValueError('case IDs must be unique')
  seen.add(case.case_id);cases.append(case)
 return tuple(cases)
def _diagnostic(message):return message
def grade_case(case:EvaluationCase,actual:Mapping[str,object]|None)->EvaluationOutcome:
 if actual is None:return EvaluationOutcome(case.case_id,case.category,False,('No actual result supplied for case.',))
 if not isinstance(actual,Mapping):return EvaluationOutcome(case.case_id,case.category,False,('Actual result must be a mapping.',))
 issues=[];expected=case.expected
 if 'required_tool' in expected and actual.get('tool_name')!=expected['required_tool']:issues.append('tool_name did not match required_tool.')
 if 'tool_arguments' in expected:
  args=actual.get('tool_arguments');
  if not isinstance(args,Mapping):issues.append('tool_arguments were not supplied.')
  else:
   for key,value in expected['tool_arguments'].items():
    if args.get(key)!=value:issues.append(f'tool_arguments.{key} did not match.')
 if 'schema_valid' in expected and actual.get('schema_valid') is not expected['schema_valid']:issues.append('schema_valid did not match.')
 if 'decision' in expected and actual.get('decision')!=expected['decision']:issues.append('decision did not match.')
 if 'required_evidence_ids' in expected and not set(expected['required_evidence_ids']).issubset(set(actual.get('evidence_ids',[]))):issues.append('required evidence IDs were missing.')
 if 'forbidden_terms' in expected:
  text=str(actual.get('text','')).lower()
  if any(term.lower() in text for term in expected['forbidden_terms']):issues.append('forbidden term detected.')
 if 'requires_clarification' in expected and actual.get('requires_clarification') is not expected['requires_clarification']:issues.append('requires_clarification did not match.')
 if 'max_tool_steps' in expected and (not isinstance(actual.get('tool_steps'),int) or actual['tool_steps']>expected['max_tool_steps']):issues.append('tool_steps exceeded limit.')
 return EvaluationOutcome(case.case_id,case.category,not issues,tuple(issues))
def run_evaluations(cases:Sequence[EvaluationCase],actual_results:Mapping[str,Mapping[str,object]])->EvaluationReport:return EvaluationReport(tuple(grade_case(case,actual_results.get(case.case_id)) for case in cases))
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description='Load an offline evaluation dataset; does not call a model.')
 parser.add_argument('dataset',type=Path);args=parser.parse_args();cases=load_cases(args.dataset);print(json.dumps({'loaded_cases':len(cases),'categories':sorted({x.category for x in cases})}))
