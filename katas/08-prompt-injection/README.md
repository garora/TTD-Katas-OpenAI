# Kata 08 — Defend Against Prompt Injection in Untrusted Content

## Learning goal

Build and test application controls that treat retrieved documents, supplier notes, tool results, and user-provided text as **untrusted data**. The content may inform a response, but it cannot rewrite policy, add capabilities, authorize a tool, override a budget, or request a secret.

This kata does **not** claim that formatting or one system prompt solves prompt injection. It models defense in depth: trusted policy/configuration is application-owned; untrusted reference data is visibly delimited; tool dispatch consults only an explicit allow-list; protected values are never inserted into the model/tool context.

## Public API

```python
context = build_context(
    policy_text="Use verified catalog facts only.",
    allowed_tools={"get_supplier_quote"},
    reference=UntrustedReference("supplier-note", note_text),
)

result = dispatch_tool("get_supplier_quote", {"sku": "workshop-13"}, context, handlers)
```

`ContextEnvelope.render_for_model()` emits trusted configuration followed by JSON-encoded untrusted data. `dispatch_tool()` reads only `context.allowed_tools`; it never parses reference content as authority and never passes the reference document to a handler.

## Threat model for this exercise

| Untrusted text tries to… | Application control |
| --- | --- |
| “Ignore policy” | Policy remains in the trusted section; document is data only. |
| Request an API key | Protected values are not represented in the envelope or handler arguments. |
| Authorize `wire_transfer` | Allow-list rejects it before dispatch. |
| Raise the budget/deadline | The trusted policy value does not change. |
| Mix a real fact with hostile prose | Structured fact extraction can retain the fact without granting the prose authority. |

## Red → green → refactor progression

1. **Red:** Render policy and reference data in separate labelled sections.
2. **Red:** JSON-encode untrusted content after a fixed data marker.
3. **Red:** Preserve a legitimate simple fact from a note alongside hostile prose.
4. **Red:** Reject a requested tool outside the trusted allow-list before a handler runs.
5. **Red:** Dispatch an allow-listed tool with explicit caller arguments only—not the document.
6. **Red:** Ensure a secret-requesting document cannot select/provide a secret value.
7. **Red:** Show a failed handler without exposing its private error text.

## Fixtures

Representative hostile inputs live in `tests/fixtures/adversarial-prompts/`. They are deliberately synthetic and contain no real credentials or customer data.

## Run the kata

```powershell
python -m unittest discover -s katas/08-prompt-injection -p "test_*.py" -v
```

Use `KATA_MODULE=starter` to make the learner scaffold red.

## Limitations

Prompt injection is risk management, not a solved string-formatting problem. This kata protects a narrow local boundary. Production systems additionally need least-privilege tools, authentication, approval workflows for consequential actions, output validation, secret isolation, logging, rate limits, retrieval controls, and ongoing adversarial evaluation.

## Definition of done

- [ ] Untrusted reference content is explicitly delimited and data-encoded.
- [ ] Trusted policy/capabilities cannot be changed by reference text.
- [ ] Unauthorized tools are rejected before handler invocation.
- [ ] Handlers receive explicit arguments only, not raw reference text or protected values.
- [ ] Legitimate facts may remain available as data.
- [ ] No API, secret, or network dependency exists.
