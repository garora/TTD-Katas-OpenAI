import importlib,os,unittest
from pathlib import Path
m=importlib.import_module(os.getenv("KATA_MODULE","solution"));L=m.load_language_matrix;G=m.grade_language_case
P=Path(__file__).resolve().parents[2]/"evals/datasets/language_matrix.jsonl"
class MultilingualTests(unittest.TestCase):
 def test_loads_representative_language_matrix(self):
  rows=L(P);self.assertEqual(len(rows),5);self.assertEqual({r["script"] for r in rows},{"latin","devanagari","han","arabic"})
 def test_grades_english_latin_terms_and_number(self):
  c=L(P)[0];self.assertTrue(G(c,{"locale":"en-US","text":"Workshop order 25"})["passed"])
 def test_grades_indic_script(self):
  c=L(P)[1];self.assertTrue(G(c,{"locale":"hi-IN","text":"लैपटॉप 25"})["passed"])
 def test_grades_cjk_and_rtl_scripts(self):
  for c,text in ((L(P)[2],"台 25"),(L(P)[3],"حاسوب 25")):
   with self.subTest(c=c["id"]):self.assertTrue(G(c,{"locale":c["locale"],"text":text})["passed"])
 def test_reports_locale_script_term_and_number_mismatch(self):
  c=L(P)[1];g=G(c,{"locale":"en-US","text":"laptop 24"});self.assertIn("locale mismatch",g["issues"]);self.assertIn("script expectation missing",g["issues"])
 def test_rejects_bad_matrix_locale_or_duplicate_id(self):
  bad=P.parent/"bad_languages.jsonl";bad.write_text("{\"id\":\"x\",\"locale\":\"English\"}\n{\"id\":\"x\",\"locale\":\"en\"}\n",encoding="utf-8")
  with self.assertRaises(ValueError):L(bad)
  bad.unlink()
if __name__=="__main__":unittest.main()
