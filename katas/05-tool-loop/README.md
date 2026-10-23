# Kata 05 — Build a Safe Tool-Execution Loop

## Learning goal

Build the application-owned orchestration loop that turns a model's proposed tool calls into bounded, validated deterministic work.

The model can request an action. The application validates the request, executes an allow-listed handler, normalizes the result, and gives that result back to the model adapter. The loop ends only with a terminal response or a structured failure. It must never silently loop forever, dispatch an unknown tool, or expose private handler details.

This kata uses a `ScriptedModelClient` with synthetic events. It never calls an API or a network service.

## Public API

```python
run_tool_loop(
    user_message: str,
    *,
    model_client: ToolLoopClient,
    tools: Mapping[str, ToolHandler],
    max_tool_steps: int = 4,
) -> ToolLoopResult
```

Model events are either:

```python
TerminalEvent(text="The quote is ready.")
ToolCallEvent(call_id="call-1", name="get_supplier_quote", arguments={"sku": "workshop-13"})
```

A completed result carries the terminal text, each validated tool call, and each normalized tool result. A failed result carries a stable, non-sensitive error code and any previously completed calls/results.

## Event flow

```text
1. start_turn(user_message)
2. terminal event? → completed result
3. tool-call event? → check step limit
4. validate tool name and argument mapping
5. invoke exactly one allow-listed handler
6. normalize {call_id, name, output, source}
7. continue_after_tool(normalized_result)
8. repeat until terminal or structured failure
```

The loop owns the sequence. Tool handlers do not call the model and the model does not directly invoke a handler.

## Red → green → refactor progression

1. **Red:** A terminal model event returns a completed result without a tool call.
   - **Green:** Handle `TerminalEvent` before dispatch logic.
   - **Refactor:** Keep terminal text validation small and explicit.
2. **Red:** One valid tool call invokes its registered handler once.
   - **Green:** Validate the allow-list and argument mapping before calling it.
   - **Refactor:** Preserve `call_id`, name, output, and source in a stable result.
3. **Red:** The normalized result is returned to the model adapter.
   - **Green:** Call `continue_after_tool` with the normalized result.
   - **Refactor:** Separate output normalization from dispatch.
4. **Red:** Sequential calls work until a terminal response arrives.
   - **Green:** Repeat the controlled loop.
   - **Refactor:** Keep the history observable in order.
5. **Red:** Unknown tools and malformed arguments fail before a handler runs.
   - **Green:** Return a structured failed result.
   - **Refactor:** Never use an unsupported model event as a fallback action.
6. **Red:** Handler exceptions and malformed handler results fail safely.
   - **Green:** Do not expose exception text or invented tool output.
   - **Refactor:** Preserve completed prior results for diagnosis.
7. **Red:** Repeated calls exceed `max_tool_steps`.
   - **Green:** Stop before dispatching the excess call.
   - **Refactor:** Make the limit a validated configuration input.

## Run the kata

Run the reference solution:

```powershell
python -m unittest discover -s katas/05-tool-loop -p "test_*.py" -v
```

To practice against the deliberately incomplete starter:

```powershell
$env:KATA_MODULE = "starter"
python -m unittest discover -s katas/05-tool-loop -p "test_*.py" -v
```

Remove `KATA_MODULE` afterwards or select **Reference solution** in Kata Studio.

## Definition of done

- [ ] Terminal, single-tool, and sequential-tool flows are covered.
- [ ] Tools are selected from the registered allow-list only.
- [ ] Non-mapping arguments never reach a handler.
- [ ] Every successful result passed to the model has `call_id`, name, output, and source.
- [ ] Unknown tools, invalid events, handler exceptions, and malformed handler results have stable failed outcomes.
- [ ] `max_tool_steps` is explicit, positive, and prevents excess dispatch.
- [ ] Error outcomes do not contain private exception text.
- [ ] All tests pass offline without credentials or network access.

## Connection to later katas

Kata 06 will keep business decisions such as budget and delivery rules out of this loop. Kata 07 will add durable session/turn identity. This kata is only responsible for bounded event-to-tool orchestration.
