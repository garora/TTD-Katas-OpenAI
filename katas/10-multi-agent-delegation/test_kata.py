from __future__ import annotations
import importlib,os,threading,time,unittest
m=importlib.import_module(os.getenv('KATA_MODULE','solution'));Task=m.DelegationTask;Result=m.DelegationResult;delegate=m.delegate_procurement_review
class Delegate:
 def __init__(self,role,status='completed',findings=None):self.role=role;self.status=status;self.findings=findings or {'ok':True};self.tasks=[]
 def __call__(self,task):self.tasks.append(task);return Result(task.task_id,task.role,self.status,self.findings if self.status=='completed' else None,'timeout' if self.status=='timed_out' else 'child issue')
class DelegationTests(unittest.TestCase):
 def args(self):return {'total_usd':27475,'lead_days':7},{'budget_usd':30000,'max_lead_days':10}
 def test_creates_two_distinct_role_tasks_with_shared_facts(self):
  q,r=self.args();b,t=Delegate('budget'),Delegate('technical');s=delegate(q,r,{'budget':b,'technical':t});self.assertEqual([x.task_id for x in s.tasks],['budget-review','technical-review']);self.assertEqual(b.tasks[0].shared_facts['quote_facts'],q);self.assertEqual(t.tasks[0].shared_facts['requirements'],r)
 def test_collects_correlated_completed_results_and_ready_summary(self):
  q,r=self.args();s=delegate(q,r,{'budget':Delegate('budget',findings={'within_budget':True}),'technical':Delegate('technical',findings={'missing':['memory_gb']})});self.assertEqual(s.status,'ready');self.assertEqual([x.task_id for x in s.results],['budget-review','technical-review']);self.assertEqual(s.uncertainties,())
 def test_failure_becomes_uncertainty_not_invented_finding(self):
  q,r=self.args();s=delegate(q,r,{'budget':Delegate('budget'),'technical':Delegate('technical','failed')});x=s.results[1];self.assertEqual(s.status,'needs_follow_up');self.assertEqual(x.findings,None);self.assertIn('child issue',s.uncertainties)
 def test_timeout_becomes_uncertainty(self):
  q,r=self.args();s=delegate(q,r,{'budget':Delegate('budget','timed_out'),'technical':Delegate('technical')});self.assertEqual(s.results[0].status,'timed_out');self.assertEqual(s.status,'needs_follow_up')
 def test_missing_delegate_is_deferred(self):
  q,r=self.args();s=delegate(q,r,{'budget':Delegate('budget')});self.assertEqual(s.results[1].status,'deferred');self.assertIn('not registered',s.uncertainties[0])
 def test_exception_is_failed_without_private_detail(self):
  def broken(task):raise RuntimeError('private database error')
  q,r=self.args();s=delegate(q,r,{'budget':broken,'technical':Delegate('technical')});self.assertEqual(s.results[0].status,'failed');self.assertNotIn('private',str(s.to_dict()))
 def test_invalid_correlation_cannot_be_claimed_completed(self):
  q,r=self.args();bad=lambda task:Result('other','budget','completed',{'x':1});s=delegate(q,r,{'budget':bad,'technical':Delegate('technical')});self.assertEqual(s.results[0].status,'failed');self.assertEqual(s.status,'needs_follow_up')
 def test_concurrency_limit_is_validated(self):
  q,r=self.args()
  for v in (0,-1,True,'2'):
   with self.subTest(v=v):
    with self.assertRaises(ValueError):delegate(q,r,{},v)
 def test_concurrency_limit_is_observable(self):
  q,r=self.args();active=0;maximum=0;lock=threading.Lock()
  def work(task):
   nonlocal active,maximum
   with lock:active+=1;maximum=max(maximum,active)
   time.sleep(.03)
   with lock:active-=1
   return Result(task.task_id,task.role,'completed',{'role':task.role})
  delegate(q,r,{'budget':work,'technical':work},max_concurrency=1);self.assertEqual(maximum,1)
 def test_summary_is_machine_readable_and_keeps_direct_facts_separate(self):
  q,r=self.args();s=delegate(q,r,{'budget':Delegate('budget'),'technical':Delegate('technical')});d=s.to_dict();self.assertEqual(d['quote_facts'],q);self.assertEqual(d['results'][0]['findings'],{'ok':True});self.assertNotIn('recommendation',d)
if __name__=='__main__':unittest.main()
