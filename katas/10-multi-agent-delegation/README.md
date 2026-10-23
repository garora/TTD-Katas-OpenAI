# Kata 10 — Test Multi-Agent Delegation and Result Aggregation

## Learning goal

Model delegation as explicit task records and bounded deterministic worker calls. A root workflow must provide each specialist with the facts it needs, correlate results to task IDs, wait for outcomes, and state uncertainty honestly when a child fails or times out.

This kata uses local fake delegates. It does not call an LLM, API, or network service.

## Public API

```python
summary = delegate_procurement_review(
    quote_facts={"total_usd": 27475, "lead_days": 7},
    requirements={"budget_usd": 30000, "max_lead_days": 10},
    delegates={"budget": budget_delegate, "technical": technical_delegate},
    max_concurrency=2,
)
```

Two tasks are always created: `budget-review` and `technical-review`. They receive shared quote/requirements plus role-specific context. `DelegationSummary` contains original facts, correlated child results, and an aggregate state:

- `ready`: both children completed;
- `needs_follow_up`: one or more child results failed, timed out, were deferred, or could not be started.

## Rules

- A root cannot claim completion for a missing child result.
- Child output is a conclusion, not a direct quote fact.
- Failures/timeouts become uncertainty; never invented findings.
- `max_concurrency` bounds the executor's workers.

## Run

```powershell
python -m unittest discover -s katas/10-multi-agent-delegation -p "test_*.py" -v
```

Use `KATA_MODULE=starter` for the incomplete scaffold.
