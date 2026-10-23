from __future__ import annotations
import importlib,os,unittest
m=importlib.import_module(os.getenv("KATA_MODULE","solution")); InMemorySessionStore=m.InMemorySessionStore; TurnStatus=m.TurnStatus
class SessionStateTests(unittest.TestCase):
 def setUp(self): self.store=InMemorySessionStore()
 def test_first_turn_creates_explicit_session_and_open_turn(self):
  turn=self.store.open_turn("chat-a","quote:13:25"); self.assertEqual(turn.session_id,"session-0001"); self.assertEqual(turn.turn_id,"turn-0001"); self.assertEqual(turn.status,TurnStatus.OPEN); self.assertTrue(turn.should_execute)
 def test_follow_up_reuses_session_and_creates_new_turn(self):
  first=self.store.open_turn("chat-a","one"); second=self.store.open_turn("chat-a","two"); self.assertEqual(first.session_id,second.session_id); self.assertNotEqual(first.turn_id,second.turn_id)
 def test_different_chats_are_isolated(self):
  a=self.store.open_turn("chat-a","one"); b=self.store.open_turn("chat-b","one"); self.assertNotEqual(a.session_id,b.session_id)
 def test_completed_action_is_not_replayed_after_refresh_or_reconnect(self):
  first=self.store.open_turn("chat-a","quote:13:25"); completed=self.store.complete_turn(first.turn_id); replay=self.store.open_turn("chat-a","quote:13:25"); self.assertEqual(completed.turn_id,replay.turn_id); self.assertFalse(replay.should_execute); self.assertEqual(replay.status,TurnStatus.COMPLETED)
 def test_distinct_completed_actions_can_run_in_same_session(self):
  one=self.store.open_turn("chat-a","quote:13:25"); self.store.complete_turn(one.turn_id); two=self.store.open_turn("chat-a","quote:14:25"); self.assertTrue(two.should_execute); self.assertEqual(one.session_id,two.session_id)
 def test_failed_turn_keeps_current_session_and_allows_retry(self):
  first=self.store.open_turn("chat-a","quote:13:25"); failed=self.store.fail_turn(first.turn_id); retry=self.store.open_turn("chat-a","quote:13:25"); self.assertEqual(failed.status,TurnStatus.FAILED); self.assertEqual(first.session_id,retry.session_id); self.assertNotEqual(first.turn_id,retry.turn_id); self.assertTrue(retry.should_execute)
 def test_expired_session_is_missing_then_new_turn_creates_new_session(self):
  first=self.store.open_turn("chat-a","one"); self.store.expire_session("chat-a"); self.assertIsNone(self.store.current_session("chat-a")); next_turn=self.store.open_turn("chat-a","two"); self.assertNotEqual(first.session_id,next_turn.session_id)
 def test_historical_turn_survives_session_expiry_for_diagnosis(self):
  turn=self.store.open_turn("chat-a","one"); self.store.complete_turn(turn.turn_id); self.store.expire_session("chat-a"); self.assertEqual(self.store.get_turn(turn.turn_id).status,TurnStatus.COMPLETED)
 def test_unknown_or_non_open_turn_transitions_fail_explicitly(self):
  with self.assertRaisesRegex(ValueError,"unknown turn"):self.store.complete_turn("missing")
  turn=self.store.open_turn("chat-a","one");self.store.complete_turn(turn.turn_id)
  with self.assertRaisesRegex(ValueError,"not open"):self.store.fail_turn(turn.turn_id)
 def test_blank_identity_inputs_are_rejected(self):
  for args in (("","action"),("chat"," ")):
   with self.subTest(args=args):
    with self.assertRaises(ValueError):self.store.open_turn(*args)
if __name__=='__main__':unittest.main()
