# Kata 04 — Test Tool Selection and Clarification Behavior

## Learning goal

Learn to test the observable boundary between a model's **proposed action** and the application's **authorized, validated action**.

A model may suggest a tool call or a clarification question. It does not directly execute anything. Application code must validate the proposed tool name and arguments against an application-owned allow-list and schema before invoking a deterministic handler.

This kata uses a recorded fake model client. It makes no OpenAI request, requires no API key, and does not test exact assistant wording.

## Public API

```python
run_tool_selection(
    user_request: str,
    *,
    model_client: ToolSelectionClient,
    tools: Mapping[str, ToolHandler],
) -> ToolSelectionResult
```

A model client returns one of these intents:

```python
ToolCallIntent(name="get_supplier_quote", arguments={"sku": "workshop-13", "quantity": 25})
ClarificationIntent(missing_fields=("budget", "delivery deadline"))
```

The application returns a stable result with one of three statuses:

| Status | Meaning | Was a tool handler invoked? |
| --- | --- | --- |
| `tool_called` | An allow-listed intent had valid arguments and its handler returned a mapping. | Yes |
| `clarification` | The model asked for missing requirements. | No |
| `rejected` | A model proposal was malformed, unauthorized, or failed safely. | No for validation/authorization failures |

## The boundary to practice

```text
User request
   ↓
Recorded fake-model event (intent only)
   ↓
Application allow-list + schema validation
   ↓
Deterministic tool handler OR clarification/rejection result
```

The model intent is **not** proof that a tool call is safe. The deterministic application layer owns permissions, argument validation, and handler dispatch.

## Red → green → refactor progression

1. **Red:** A complete quote intent invokes `get_supplier_quote` with the exact validated arguments.
   - **Green:** Route a valid allow-listed tool intent to its handler.
   - **Refactor:** Preserve an observable tool name, arguments, and handler result in the outcome.
2. **Red:** A broad request produces a clarification outcome.
   - **Green:** Return a structured clarification status with requested fields.
   - **Refactor:** Do not assert or store one specific natural-language question.
3. **Red:** A zero/negative/string quantity is rejected before the quote handler is invoked.
   - **Green:** Validate required fields and integer semantics at the dispatch boundary.
   - **Refactor:** Extract small schema validators.
4. **Red:** An unknown tool or discount tool is rejected before handler dispatch.
   - **Green:** Enforce one application-owned allow-list.
   - **Refactor:** Keep authorization errors distinct from model/handler errors.
5. **Red:** Extra fields or invalid SKU values do not silently reach a handler.
   - **Green:** Reject arguments that do not match the documented quote schema.
   - **Refactor:** Make error outcomes JSON-serializable and useful to an orchestrator.
6. **Red:** A handler failure becomes a safe rejected outcome rather than invented data.
   - **Green:** Catch the handler exception at the boundary without returning its private details.
   - **Refactor:** Record private details only in a server-side log if a production application needs them; keep them out of the normalized result.

## Run the kata

The checked-in tests use `solution.py` so repository validation remains green. To work through the exercise, select **Starter (exercise)** in Kata Studio or use the environment variable locally:

```powershell
$env:KATA_MODULE = "starter"
python -m unittest discover -s katas/04-tool-selection -p "test_*.py" -v
```

For the reference solution:

```powershell
Remove-Item Env:KATA_MODULE -ErrorAction SilentlyContinue
python -m unittest discover -s katas/04-tool-selection -p "test_*.py" -v
```

## Definition of done

- [ ] A recorded complete quote intent calls only `get_supplier_quote` with the expected `sku` and positive `quantity`.
- [ ] A clarification intent produces a structured clarification result without tool arguments or handler execution.
- [ ] Unknown, unauthorized, and malformed tool calls are rejected before a handler runs.
- [ ] The quote schema rejects missing/extra arguments, blank SKU values, booleans, non-integers, zero, and negative quantities.
- [ ] A tool-handler exception cannot become invented quote data or an unhandled raw error response.
- [ ] Tests assert state, tool calls, arguments, and outcomes—not exact model prose.
- [ ] Everything passes offline with no API key or network dependency.

## Connection to later katas

Kata 05 will extend this single-step decision into a bounded tool loop. Keep this kata's result contract narrow: it represents one normalized model intent and one validated application response.
