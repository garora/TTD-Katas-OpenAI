# Kata 07 — Test Session State and Turn Lifecycle

## Learning goal

Treat a chat/session/turn lifecycle as explicit application state—not as invisible model memory. This kata builds an in-memory session service with stable identities, completed-action deduplication, turn outcomes, and explicit session expiry.

No provider session, model SDK, network request, or global process state is used. The service is a deterministic local seam that a later provider adapter could implement behind the same behavior.

## Public API

```python
store = InMemorySessionStore()
turn = store.open_turn(chat_id="chat-a", action_key="quote:workshop-13:25")

if turn.should_execute:
    # Perform the idempotent local action once.
    store.complete_turn(turn.turn_id)
else:
    # A refresh/reconnect saw an already-completed action; do not replay it.
    pass
```

`TurnContext` carries a `chat_id`, `session_id`, `turn_id`, `action_key`, and `should_execute` flag. Turn and session identities are independent from transcript text.

## State transitions

```text
open_turn(chat, action)
  ├─ no active session      → create session, create open turn
  ├─ existing chat session  → reuse session, create open turn
  └─ completed action key   → return existing completed turn; should_execute = False

complete_turn(turn) → record completed action for that session
fail_turn(turn)     → record failure; keep the session valid; allow a new attempt
expire_session(chat) → remove active session reference; historical turns remain inspectable
```

A refresh/reconnect must not silently replay a successful action. A failed action is not considered completed, so a deliberate retry can create a new turn against the same valid session.

## Red → green → refactor progression

1. **Red:** First turn for a chat creates a session and turn.
2. **Red:** Next turn for the same chat reuses the session but has a new turn ID.
3. **Red:** A different chat receives a distinct session.
4. **Red:** Completion records action metadata and blocks a reconnect replay.
5. **Red:** A failed turn preserves the current session and allows a retry.
6. **Red:** Expiry removes only the active session reference; a new turn creates a new session.
7. **Red:** Invalid/unknown turn operations fail explicitly.

## Run the kata

```powershell
python -m unittest discover -s katas/07-session-state -p "test_*.py" -v
```

Set `KATA_MODULE=starter` to run the same tests against the incomplete learner scaffold.

## Definition of done

- [ ] Chat, session, turn, and action-key identities are explicit typed fields.
- [ ] New chats create sessions; follow-ups reuse them; other chats isolate them.
- [ ] Completed actions are not replayed by reconnect/refresh.
- [ ] Failed turns keep a valid session and permit an explicit retry.
- [ ] Expiry/missing-session behavior is deterministic and testable.
- [ ] Historical turn metadata remains available after expiry.
- [ ] All tests run offline.
