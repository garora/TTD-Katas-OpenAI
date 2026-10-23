from __future__ import annotations
import json
from pathlib import Path
from evals.audio_grading import contains_script,language_tag_is_valid,numbers_in_text,normalize_text
def load_language_matrix(path:Path):
 rows=[];seen=set()
 for line in path.read_text(encoding="utf-8").splitlines():
  if not line.strip():continue
  row=json.loads(line)
  if row.get("id") in seen or not language_tag_is_valid(row.get("locale","").lower()):raise ValueError("invalid language matrix row")
  seen.add(row["id"]);rows.append(row)
 return tuple(rows)
def grade_language_case(case:dict,actual:dict):
 if not isinstance(case,dict) or not isinstance(actual,dict):raise ValueError("case and actual must be mappings")
 issues=[];text=actual.get("text","")
 if actual.get("locale")!=case.get("locale"):issues.append("locale mismatch")
 if not contains_script(text,case.get("script","latin")):issues.append("script expectation missing")
 norm=normalize_text(text)
 for term in case.get("required_terms",[]):
  if normalize_text(term) not in norm:issues.append(f"missing term: {term}")
 for number in case.get("required_numbers",[]):
  if number not in numbers_in_text(text):issues.append(f"missing number: {number}")
 return {"passed":not issues,"issues":issues,"locale":case.get("locale")}
