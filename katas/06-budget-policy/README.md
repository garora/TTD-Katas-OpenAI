# Kata 06 — Keep Budget and Delivery Policy Deterministic

## Learning goal

Build a pure procurement-policy function that decides whether a validated quote is within budget and delivery constraints.

A language model may explain the result in a friendly way, but it must not be the authority for deterministic limits, calculations, or approval decisions. The application computes the result once in conventional code, returns structured reasons, and lets later layers present that already-computed decision.

This kata has no model client, SDK, tool, API key, or network dependency.

## Public API

```python
evaluate_quote(quote: Quote, policy: ProcurementPolicy) -> PolicyDecision
```

Inputs:

```python
Quote(
    sku="workshop-13",
    quantity=25,
    unit_price_usd=1099,
    lead_days=7,
)

ProcurementPolicy(
    budget_usd=30_000,
    max_lead_days=10,
)
```

Output:

```python
PolicyDecision(
    decision=Decision.APPROVE,
    reasons=(),
)
```

or, for a failed policy:

```python
PolicyDecision(
    decision=Decision.REJECT,
    reasons=(
        PolicyReason(ReasonCode.BUDGET_EXCEEDED, "total_usd", 30_001, 30_000),
        PolicyReason(ReasonCode.LEAD_TIME_EXCEEDED, "lead_days", 11, 10),
    ),
)
```

## Currency and quantity assumptions

- Currency values are **non-negative whole US dollars** represented by Python `int`; no floats or rounding are accepted.
- `quantity` is a positive whole-unit count.
- Quote total is always `quantity × unit_price_usd`.
- The kata intentionally excludes tax, shipping, currency conversion, discounts, and partial orders. Add those as explicit inputs/rules in a future domain exercise—never as hidden model reasoning.
- A quote exactly equal to the budget and/or delivery deadline is allowed.

## Red → green → refactor progression

1. **Red:** Approve a quote under both constraints.
   - **Green:** Return `APPROVE` with no reasons.
   - **Refactor:** Keep policy evaluation independent of presentation text.
2. **Red:** Reject a quote above the budget.
   - **Green:** Add a machine-readable `BUDGET_EXCEEDED` reason.
   - **Refactor:** Include observed and limit values in the reason.
3. **Red:** Reject a quote past the delivery deadline.
   - **Green:** Add a `LEAD_TIME_EXCEEDED` reason.
   - **Refactor:** Preserve a stable reason order.
4. **Red:** Report both failures when both constraints are exceeded.
   - **Green:** Accumulate reasons rather than returning at the first violation.
   - **Refactor:** Keep decision logic small and pure.
5. **Red:** Confirm boundary equality passes.
   - **Green:** Use strict `>` comparisons for limits.
   - **Refactor:** Name the constraints clearly.
6. **Red:** Reject malformed monetary/quantity/policy input at construction time.
   - **Green:** Validate types, booleans, and ranges in typed input models.
   - **Refactor:** Reuse small integer/text validators.
7. **Red:** Serialize the decision for a future explanation layer.
   - **Green:** Return a stable dictionary shape with decision and structured reasons.
   - **Refactor:** Do not add model prose to the policy object.

## Let a model explain—not decide

The deterministic policy runs first:

```python
result = evaluate_quote(quote, policy)
assert result.decision is Decision.REJECT
```

A later presentation request can contain the result as facts:

```text
Explain this already-computed procurement decision. Do not alter it.
Decision: reject
Reason: total_usd is 30001; budget limit is 30000.
```

The model may make that explanation easier to read, but application code remains the sole authority for `approve` or `reject`.

## Run the kata

Reference solution:

```powershell
python -m unittest discover -s katas/06-budget-policy -p "test_*.py" -v
```

Deliberately incomplete starter:

```powershell
$env:KATA_MODULE = "starter"
python -m unittest discover -s katas/06-budget-policy -p "test_*.py" -v
```

## Definition of done

- [ ] Approval, budget rejection, deadline rejection, both reasons, and equality boundaries have tests.
- [ ] Quotes/policy use validated whole-number USD and unit-count values.
- [ ] The evaluator is a pure function with no external side effects.
- [ ] Results contain a decision and structured reasons, not only prose.
- [ ] Reason order and observed/limit values are stable.
- [ ] A model explanation example receives policy facts but does not make the policy decision.
- [ ] All tests pass offline.

## Connection to later katas

Kata 07 will add session state without changing this policy's deterministic nature. Keep this evaluator side-effect-free so it remains easy to test, explain, and reuse.
