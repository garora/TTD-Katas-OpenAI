# Kata 02 — Validate Structured Model Output

## Learning goal

Build a deterministic boundary that converts a model response into a typed procurement recommendation. Applications should use structured output when they require fields that drive code, tools, policy, or a UI. Free-form prose may be useful for explanation, but it is not a reliable substitute for validated application data.

This kata deliberately does **not** call an OpenAI API. Learners parse supplied JSON or mapping values, validate them, and produce either a typed `Recommendation` or a useful `RecommendationValidationError`. A future model adapter can use that error to request a repair, but it must never silently accept malformed output.

## Public API

```python
parse_recommendation(payload: str | Mapping[str, object]) -> Recommendation
```

The returned immutable `Recommendation` contains:

```python
Recommendation(
    sku: str,
    total_usd: int,
    lead_days: int,
    decision: Decision,  # APPROVE, REJECT, or NEEDS_CLARIFICATION
    uncertainties: tuple[str, ...],
)
```

`RecommendationValidationError` is raised for invalid JSON, non-object payloads, missing fields, invalid types, invalid values, or unsupported decisions. Its message names the field/problem so a caller can record it or provide it to a repair flow.

## Red → green → refactor progression

1. **Red:** Parse a complete valid JSON object into a `Recommendation`.
   - **Green:** Decode JSON and construct the typed value.
   - **Refactor:** Separate parsing from field validation.
2. **Red:** Accept a mapping as well as a JSON string.
   - **Green:** Normalize both forms into one validation path.
   - **Refactor:** Keep the public API narrow and documented.
3. **Red:** Reject missing required fields.
   - **Green:** Validate all required keys before construction.
   - **Refactor:** Provide a consistent field-specific error format.
4. **Red:** Reject incorrect types and invalid numeric values.
   - **Green:** Validate integer—not boolean—price/lead-time values and reject negatives.
   - **Refactor:** Extract reusable validators.
5. **Red:** Restrict decisions to the approved enum values.
   - **Green:** Convert known strings to `Decision`.
   - **Refactor:** Make permitted values discoverable in the type.
6. **Red:** Require a list of non-blank uncertainty strings.
   - **Green:** Normalize it into an immutable tuple.
   - **Refactor:** Make serialization round-trip cleanly.

## Run the kata

This exercise has no external dependencies, API key, or network request.

```powershell
python -m unittest discover -s katas/02-structured-output -p "test_*.py" -v
```

The checked-in tests default to `solution.py` so repository validation stays green. To work through the kata, set `KATA_MODULE=starter` before running the tests, or copy the starter to your own working module.

```powershell
$env:KATA_MODULE = "starter"
python -m unittest discover -s katas/02-structured-output -p "test_*.py" -v
```

## Why this matters for OpenAI applications

Prompting can encourage a model to emit valid JSON, but the application still owns validation. Schema validation protects downstream code from absent fields, type errors, invented decision values, and free-form responses. It also provides an observable contract for TDD: test the parsed fields and errors, rather than requiring an exact model-generated sentence.

## Definition of done

- [ ] Valid JSON and mappings produce a typed recommendation.
- [ ] Invalid JSON and non-object JSON are rejected.
- [ ] Every required field is validated.
- [ ] Price and lead-time types/values are checked before use.
- [ ] Decisions are limited to the approved enum values.
- [ ] Uncertainties are validated and normalized.
- [ ] Errors are useful for diagnosis or a future repair attempt.
- [ ] All tests pass offline.
