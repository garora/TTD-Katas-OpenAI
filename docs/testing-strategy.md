# Testing Strategy

OpenAI applications need a layered test strategy. Most behavior should be verified offline with deterministic fixtures. Live-model checks are valuable, but they are variable, slower, cost money, and must never be the only protection against regressions.

## Testing pyramid

```text
                 /-------------------\
                / Optional live evals \   Small, deliberate, monitored
               /-----------------------\
              / Dataset / rubric evals  \ Versioned behavioral regression cases
             /---------------------------\
            / Contract + integration fakes \ Provider-event and tool-loop behavior
           /---------------------------------\
          /           Unit tests              \ Pure logic, fastest, default CI
         /-------------------------------------\
```

## Default rule

The default test command must be:

- credential-free;
- network-free;
- deterministic and repeatable;
- fast enough for local development and CI;
- safe to run without causing external side effects.

Use fakes, local fixtures, and recorded/synthetic provider events. A real API call is never required to validate ordinary domain logic, schemas, prompt composition, tool argument validation, or orchestration state transitions.

## Test layers

| Layer | Purpose | Dependencies | Typical examples |
| --- | --- | --- | --- |
| Unit | Verify one deterministic function/class | Standard library/test framework only | Quote calculation, policy decision, JSON/schema parsing |
| Contract | Verify boundaries between application components | Fakes and fixtures | Adapter event normalization, tool-call shape, tool result schema |
| Integration | Verify local multi-component workflows | In-memory stores/fake model and tools | Tool loop, session reuse, evidence collection |
| Dataset evaluation | Verify a versioned set of behavioral expectations | Fixtures and deterministic/rubric graders | Tool selection, grounding, prompt-injection handling |
| Live evaluation | Observe a real configured model/provider | Authorized credentials and explicit opt-in | Schema validity rate, tool-call accuracy, latency, cost |

### Unit tests

Unit tests are the foundation. They should test pure behavior and use exact assertions when that behavior is deterministic.

```python
def test_quote_total_is_unit_price_times_quantity():
    quote = get_supplier_quote({"sku": "workshop-13", "quantity": 25})
    assert quote["total_usd"] == 27475
```

Good unit-test subjects include:

- prompt section ordering and data-envelope formatting;
- input/schema validation;
- catalog lookup and arithmetic;
- budget/deadline decisions;
- state-transition rules;
- evidence/claim mapping;
- timeout and maximum-step logic.

### Contract tests

Contract tests validate the shape of a boundary. They are especially useful where an application adapter receives provider events or invokes tools.

```python
def test_allowed_tool_call_is_normalized_before_dispatch(fake_model):
    fake_model.events = [tool_call("get_supplier_quote", {"sku": "workshop-13", "quantity": 25})]
    result = orchestrator.run("Quote 25 laptops")
    assert result.tool_calls[0].name == "get_supplier_quote"
```

Contract tests should verify:

- tool names are in an allow-list;
- arguments validate before handlers run;
- error/result envelopes are stable;
- streaming/provider events normalize to application models;
- structured output is validated before downstream use;
- provider SDK details do not leak across the adapter boundary.

### Integration tests with fakes

Integration tests combine local components but still avoid an external model. For example, use an in-memory session store, a fake model event stream, and real deterministic tool handlers to test a complete tool loop.

Test outcomes/state transitions—not exact wording. Assert that the correct tool was invoked, the result was sent back, a step limit halted a loop, or a failed child agent produced a deferred/uncertain state.

### Dataset evaluations

Version behavioral cases in `evals/datasets/`. Each case should identify its category and the invariants that matter.

```yaml
id: quote-workshop-13
category: tool-selection
input: Quote 25 workshop-13 laptops.
expected:
  required_tool: get_supplier_quote
  tool_arguments:
    sku: workshop-13
    quantity: 25
  required_facts:
    total_usd: 27475
```

Prefer deterministic graders whenever possible:

- schema-valid / schema-invalid;
- expected tool selected;
- exact validated argument fields;
- policy decision;
- required evidence ID/source;
- forbidden secret/unsupported claim absent;
- maximum steps not exceeded.

Use a rubric-based grader only for criteria that cannot be reduced to a deterministic rule, such as helpfulness or explanation quality. Keep the rubric specific, versioned, and separate from core safety/policy enforcement.

## Test model-facing behavior by invariant

Do **not** write brittle tests like this:

```python
assert answer == "The total is $27,475 and delivery takes 7 days."
```

Instead, validate a structured contract or stable properties:

```python
assert result.tool_calls[0].name == "get_supplier_quote"
assert result.tool_calls[0].arguments == {"sku": "workshop-13", "quantity": 25}
assert result.evidence[0].facts["total_usd"] == 27475
assert result.policy.outcome == "approve"
```

Exact prose assertions are appropriate only where the application itself deterministically renders a fixed template.

## Fixtures

Keep fixtures small, representative, and safe to commit.

| Location | Contents |
| --- | --- |
| `tests/fixtures/model-events/` | Synthetic or redacted normalized model/provider events |
| `tests/fixtures/tool-results/` | Deterministic tool success/error results |
| `tests/fixtures/adversarial-prompts/` | Injection attempts, malformed content, edge cases |
| `evals/datasets/` | Versioned end-to-end behavioral cases |

Never commit API keys, access tokens, production transcripts containing sensitive data, customer data, or secrets embedded in prompts/tool results.

## Live evaluations: explicit opt-in only

Live checks may be used to monitor a chosen model/configuration, but they are not default CI tests.

Requirements for a live evaluation runner:

1. Require an explicit command/flag such as `python scripts/run_evals.py --live`.
2. Fail fast if the required authorized credential is absent; never print it.
3. Use a small, versioned dataset with known cost and rate limits.
4. Capture model/configuration identifiers, latency, token/cost measurements when available, and grader results.
5. Apply timeouts, maximum attempts, and non-destructive tool configuration.
6. Store reports in ignored/generated output directories rather than committing transient results.
7. Report uncertainty and failures honestly; do not convert a provider outage into a product-quality conclusion.

Example live metrics:

- structured-output validity rate;
- correct tool selection and argument accuracy;
- evidence coverage / unsupported-claim rate;
- policy compliance rate;
- latency percentile;
- estimated/requested cost;
- refusal/clarification behavior for unsafe or ambiguous inputs.

## Regression workflow

When a bug occurs:

1. Reduce it to the smallest safe fixture.
2. Add a failing unit, contract, integration, or evaluation case.
3. Implement the smallest correct fix.
4. Run the appropriate offline test suite.
5. Add a live case only if the issue depends on real-provider/model behavior.
6. Record the test category and expected invariant in the related issue/PR.

Every incident-worthy behavior should become an offline regression test whenever practical.

## Suggested commands

Each kata documents its exact command. The current standalone katas use the standard library:

```powershell
python -m unittest discover -s katas/01-prompt-builder -p "test_*.py" -v
python -m unittest discover -s katas/02-structured-output -p "test_*.py" -v
python -m unittest discover -s katas/03-supplier-quote-tool -p "test_*.py" -v
```

Future repository-wide tooling may provide a single test command, but it must preserve the default offline guarantee.
