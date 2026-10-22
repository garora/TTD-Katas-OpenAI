"""Real offline subprocess and loopback-HTTP regressions for Kata Studio."""
from __future__ import annotations
import http.client
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
import uuid

from studio.registry import ROOT, load_katas, validate_target
from studio.runner import BusyError, RunManager
from studio.server import create_server
from studio.worker import scrub


class StudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name) / 'state'

    def manager(self, root=ROOT, timeout=15):
        manager = RunManager(root, self.state, timeout)
        self.addCleanup(manager.close)
        return manager

    def wait(self, manager, run_id):
        with manager.condition:
            self.assertTrue(manager.condition.wait_for(
                lambda: manager.runs[run_id][-1]['kind'] == 'run_finished', timeout=20))
        return manager.events(run_id)

    def fixture(self, body):
        root = Path(self.temp.name) / 'curriculum'
        folder = root/'katas'/'01-fixture'
        folder.mkdir(parents=True)
        (root/'studio').mkdir()
        (root/'studio'/'katas.json').write_text(json.dumps([
            {'id':'01-fixture','title':'Fixture','stages':[{'id':'run','label':'Run','functions':['work']}]}]))
        for name in ('README.md','solution.py','starter.py'):
            (folder/name).write_text('# test fixture\n')
        (folder/'test_kata.py').write_text(body)
        return root

    def test_registry_availability_matches_published_deliverables(self):
        katas = load_katas()
        self.assertEqual(len(katas), 11)
        self.assertTrue(all(k['available'] for k in katas[:3]))
        for kata in katas:
            folder = ROOT/'katas'/kata['id']
            expected = all((folder/name).is_file() for name in ('README.md','starter.py','solution.py','test_kata.py'))
            self.assertEqual(kata['available'],expected)

    def test_unknown_planned_and_path_targets_are_rejected(self):
        for kata, target in [('../outside','solution'),
                             ('01-prompt-builder','../../secrets'), ('01-prompt-builder','working')]:
            with self.subTest(kata=kata,target=target), self.assertRaises(ValueError):
                validate_target(kata,target)

    def test_working_target_is_discovered_only_when_file_exists(self):
        root = self.fixture('')
        self.assertNotIn('working',load_katas(root)[0]['targets'])
        (root/'katas'/'01-fixture'/'working.py').write_text('# local work')
        self.assertIn('working',load_katas(root)[0]['targets'])

    def test_available_solutions_execute_and_capture_real_function_traces(self):
        manager = self.manager()
        for kata in (k for k in load_katas() if k['available']):
            with self.subTest(kata=kata['id']):
                events = self.wait(manager, manager.start(kata['id'],'solution'))
                self.assertEqual(events[-1]['status'],'passed',events)
                summary = next(e for e in events if e['kind']=='suite_finished')
                self.assertGreater(summary['total'],0)
                self.assertEqual(summary['counts']['passed'],summary['total'])
                if any(stage.get('functions') for stage in kata['stages']):
                    self.assertTrue(any(e['kind']=='trace' and e['action']=='call' for e in events))
                self.assertEqual([e['seq'] for e in events],list(range(1,len(events)+1)))
                self.assertFalse(any('arguments' in e or 'locals' in e for e in events))

    def test_available_starters_are_honestly_red(self):
        manager = self.manager()
        for kata in (k for k in load_katas() if k['available']):
            events = self.wait(manager, manager.start(kata['id'],'starter'))
            self.assertEqual(events[-1]['status'],'failed')
            self.assertTrue(any(e['kind']=='test_finished' and e['status'] in {'failed','error'} for e in events))

    def test_runs_persist_and_replay_does_not_execute_tests(self):
        manager = self.manager()
        run_id = manager.start('03-supplier-quote-tool','solution')
        events = self.wait(manager,run_id)
        recovered = RunManager(ROOT,self.state)
        self.addCleanup(recovered.close)
        self.assertEqual(recovered.events(run_id),events)
        self.assertEqual(recovered.events(run_id,3),events[3:])
        self.assertIsNone(recovered.active)
        self.assertEqual(len(recovered.history()),1)

    def test_incomplete_run_is_interrupted_on_restart(self):
        self.state.mkdir()
        run_id = str(uuid.uuid4())
        first = {'kind':'run_started','seq':1,'run_id':run_id,'at':'2026-10-23T00:00:00Z',
                 'kata_id':'01-prompt-builder','target':'solution'}
        (self.state/f'{run_id}.jsonl').write_text(json.dumps(first)+'\n')
        manager = self.manager()
        self.assertEqual(manager.events(run_id)[-1]['status'],'interrupted')
        self.assertIsNone(manager.active)

    def test_timeout_and_no_overlapping_execution(self):
        root = self.fixture('import time, unittest\nclass TestSlow(unittest.TestCase):\n def test_slow(self): time.sleep(10)\n')
        manager = self.manager(root,timeout=.5)
        run_id = manager.start('01-fixture','solution')
        with self.assertRaises(BusyError):
            manager.start('01-fixture','solution')
        self.assertEqual(self.wait(manager,run_id)[-1]['status'],'timed_out')
        self.assertIsNone(manager.active)

    def test_worker_drops_credential_environment_and_blocks_network(self):
        root = self.fixture('import os,socket,unittest\nclass TestOffline(unittest.TestCase):\n def test_environment(self): self.assertNotIn("OPENAI_API_KEY",os.environ)\n def test_network(self):\n  with self.assertRaises(PermissionError): socket.getaddrinfo("example.invalid",443)\n')
        previous = os.environ.get('OPENAI_API_KEY')
        os.environ['OPENAI_API_KEY']='test-only-placeholder'
        try:
            manager = self.manager(root)
            events = self.wait(manager,manager.start('01-fixture','solution'))
            self.assertEqual(events[-1]['status'],'passed',events)
            self.assertNotIn('test-only-placeholder',json.dumps(events))
        finally:
            if previous is None: os.environ.pop('OPENAI_API_KEY',None)
            else: os.environ['OPENAI_API_KEY']=previous

    def test_subtest_failures_are_not_counted_as_success(self):
        root = self.fixture('import unittest\nclass TestSub(unittest.TestCase):\n def test_sub(self):\n  with self.subTest(case="bad"): self.assertEqual(1,2)\n')
        manager = self.manager(root)
        events = self.wait(manager,manager.start('01-fixture','solution'))
        finished = next(e for e in events if e['kind']=='test_finished')
        self.assertEqual(finished['status'],'failed')

    def test_redaction_of_credential_shaped_error_text(self):
        self.assertNotIn('x'*24,scrub('sk-'+ 'x'*24))
        self.assertEqual(scrub('api_key=example-value'), 'api_key=[REDACTED]')

    def test_planned_fixture_is_not_runnable(self):
        root = self.fixture("")
        (root/'katas'/'01-fixture'/'solution.py').unlink()
        self.assertFalse(load_katas(root)[0]['available'])
        with self.assertRaisesRegex(ValueError, 'planned'):
            validate_target('01-fixture','starter',root)

    def test_partial_last_log_line_preserves_previous_events(self):
        self.state.mkdir()
        run_id=str(uuid.uuid4())
        event={'kind':'run_started','seq':1,'run_id':run_id,'at':'2026-10-23T00:00:00Z',
               'kata_id':'01-prompt-builder','target':'solution'}
        (self.state/f'{run_id}.jsonl').write_text(json.dumps(event)+'\n{"kind":')
        manager=self.manager()
        self.assertEqual(manager.events(run_id)[0],event)
        self.assertEqual(manager.events(run_id)[-1]['status'],'interrupted')
        for line in (self.state/f'{run_id}.jsonl').read_text().splitlines():
            self.assertIsInstance(json.loads(line),dict)

    def test_pass_skip_expected_failure_and_error_have_distinct_outcomes(self):
        root=self.fixture('import unittest\nclass TestKinds(unittest.TestCase):\n def test_pass(self): self.assertTrue(True)\n @unittest.skip("exercise")\n def test_skip(self): pass\n @unittest.expectedFailure\n def test_expected(self): self.assertEqual(1,2)\n def test_error(self): raise ValueError("test fixture error")\n')
        manager=self.manager(root)
        events=self.wait(manager,manager.start('01-fixture','solution'))
        counts=next(e['counts'] for e in events if e['kind']=='suite_finished')
        self.assertEqual(counts,{'passed':1,'failed':0,'error':1,'skipped':1,'expected_failure':1})
        self.assertEqual(events[-1]['status'],'failed')

    def test_import_error_is_recorded_instead_of_becoming_a_green_run(self):
        root=self.fixture('raise ImportError("intentional fixture failure")\n')
        manager=self.manager(root)
        events=self.wait(manager,manager.start('01-fixture','solution'))
        self.assertEqual(events[-1]['status'],'failed')
        self.assertTrue(any(e.get('status')=='error' for e in events))

    def test_unknown_run_and_source_fingerprints(self):
        manager=self.manager()
        with self.assertRaises(KeyError): manager.events('unknown')
        events=self.wait(manager,manager.start('01-prompt-builder','solution'))
        self.assertEqual(events[0]['stages'],load_katas()[0]['stages'])
        self.assertTrue(all(len(value)==64 for value in events[0]['source_hashes'].values()))

    def test_http_completed_stream_always_delivers_terminal_event(self):
        server=self.server()
        for _ in range(4):
            run_id=server.manager.start('01-prompt-builder','solution')
            connection=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=15)
            connection.request('GET',f'/api/runs/{run_id}/events')
            response=connection.getresponse()
            events=[json.loads(line[6:]) for line in response.read().decode().splitlines() if line.startswith('data: ')]
            connection.close()
            self.assertEqual(events[-1]['kind'],'run_finished')
            self.assertEqual(events[-1]['status'],'passed')

    def test_second_server_cannot_recover_or_write_owned_history(self):
        first = self.server()
        with self.assertRaisesRegex(RuntimeError, 'already using'):
            create_server(0,ROOT,self.state)
        self.assertEqual(first.manager.history(), [])

    def test_state_ownership_is_released_after_server_close(self):
        first = create_server(0,ROOT,self.state)
        first.manager.close()
        first.server_close()
        second = create_server(0,ROOT,self.state)
        second.manager.close()
        second.server_close()

    def server(self, root=ROOT):
        server = create_server(0,root,self.state)
        thread = threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        def close():
            server.shutdown()
            server.manager.close()
            server.server_close()
            thread.join(3)
        self.addCleanup(close)
        return server

    def request(self,server,method,path,body=None,headers=None):
        connection = http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=15)
        connection.request(method,path,body=body,headers=headers or {})
        response = connection.getresponse()
        status, payload = response.status,response.read()
        connection.close()
        return status,payload

    def test_http_origin_host_and_static_path_restrictions(self):
        server = self.server()
        origin = f'http://127.0.0.1:{server.server_port}'
        body=json.dumps({'kata_id':'01-prompt-builder','target':'solution'})
        self.assertEqual(self.request(server,'POST','/api/runs',body,{'Content-Type':'application/json'})[0],403)
        self.assertEqual(self.request(server,'POST','/api/runs',body,{'Origin':'https://outside.invalid','Content-Type':'application/json'})[0],403)
        self.assertEqual(self.request(server,'GET','/api/katas',headers={'Host':'outside.invalid'})[0],403)
        for path in ('/../README.md','/studio/worker.py','/api/runs/not-a-run'):
            self.assertEqual(self.request(server,'GET',path)[0],404)
        self.assertEqual(self.request(server,'GET','/')[0],200)
        self.assertEqual(self.request(server,'POST','/api/runs','[]',{'Origin':origin,'Content-Type':'application/json'})[0],400)
        self.assertEqual(self.request(server,'GET','/api/katas')[0],200)

    def test_http_streams_before_completion_and_resumes_by_event_id(self):
        root=self.fixture('import time,unittest\nclass TestLive(unittest.TestCase):\n def test_live(self): time.sleep(1)\n')
        server=self.server(root)
        origin=f'http://127.0.0.1:{server.server_port}'
        status,body=self.request(server,'POST','/api/runs',json.dumps({'kata_id':'01-fixture','target':'solution'}),{'Origin':origin,'Content-Type':'application/json'})
        self.assertEqual(status,201)
        run_id=json.loads(body)['run_id']
        connection=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=10)
        connection.request('GET',f'/api/runs/{run_id}/events')
        response=connection.getresponse()
        self.assertEqual(response.status,200)
        first=[]
        while True:
            line=response.readline().decode()
            if line.startswith('data: '):
                first.append(json.loads(line[6:]))
                if first[-1]['kind']=='test_started': break
        self.assertEqual(server.manager.history()[0]['status'],'running')
        connection.close()
        all_events=self.wait(server.manager,run_id)
        connection=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=10)
        connection.request('GET',f'/api/runs/{run_id}/events',headers={'Last-Event-ID':str(first[-1]['seq'])})
        response=connection.getresponse()
        resumed=[json.loads(line[6:]) for line in response.read().decode().splitlines() if line.startswith('data: ')]
        connection.close()
        self.assertEqual(resumed,all_events[first[-1]['seq']:])
        self.assertEqual(resumed[-1]['kind'],'run_finished')


if __name__=='__main__':
    unittest.main()
