# Kata 03 — Implement the Deterministic Supplier Quote Tool

## Learning goal

Build a narrow, deterministic supplier-quote tool before connecting it to an OpenAI agent. The tool accepts validated input, looks up a small local catalog, calculates the total, and returns a JSON-serializable result with source provenance.

This exercise teaches a central design principle for AI applications: use an LLM to decide when it needs a fact or to explain a result, but use conventional code to calculate, validate, and return the fact. The catalog and quote logic stay independently testable, repeatable, and safe to call from later agent katas.

## Public API

```python
get_supplier_quote(arguments: Mapping[str, object]) -> dict[str, object]
```

Required input:

```python
{"sku": "workshop-13", "quantity": 25}
```

Successful output shape:

```python
{
    "sku": "workshop-13",
    "quantity": 25,
    "unit_price_usd": 1099,
    "total_usd": 27475,
    "lead_days": 7,
    "source": "supplier catalog",
}
```

The tool raises a typed error when the input is malformed, the quantity is not a positive integer, or the SKU is unknown. It never calls a model, network service, or external catalog.

## Starter catalog

| SKU | Unit price (USD) | Lead time |
| --- | ---: | ---: |
| `workshop-13` | 1,099 | 7 days |
| `workshop-14` | 1,399 | 10 days |
| `workshop-pro` | 1,899 | 14 days |

## Red → green → refactor progression

1. **Red:** Quote one known SKU at quantity one.
   - **Green:** Store a small catalog and return SKU, price, lead time, and source.
   - **Refactor:** Model catalog records explicitly.
2. **Red:** Calculate a quantity-based total.
   - **Green:** Return `unit_price_usd × quantity` as `total_usd`.
   - **Refactor:** Keep the calculation in one place.
3. **Red:** Reject zero and negative quantities.
   - **Green:** Validate quantity before looking up/calculating.
   - **Refactor:** Give the caller a field-specific tool-input error.
4. **Red:** Reject an unknown SKU.
   - **Green:** Raise a typed `UnknownSkuError`.
   - **Refactor:** Do not leak implementation details or invent a quote.
5. **Red:** Reject malformed input.
   - **Green:** Require a mapping, a non-blank string SKU, and an integer (not boolean) quantity.
   - **Refactor:** Extract reusable input validators.
6. **Red:** Prove the response is JSON-serializable and has stable provenance.
   - **Green:** Return only JSON-compatible primitive values.
   - **Refactor:** Document the contract for a future function-tool wrapper.

## Run the kata

No package installation, API key, model, or network access is required.

```powershell
python -m unittest discover -s katas/03-supplier-quote-tool -p "test_*.py" -v
```

Tests run against `solution.py` by default so the repository stays green. To learn via the incomplete scaffold, set `KATA_MODULE=starter` before running the test command.

## OpenAI function-tool connection

Later, an OpenAI adapter can expose this exact input/output contract to a model as a function tool. That adapter should validate the tool-call arguments before calling this function. The domain function itself remains independent of any OpenAI SDK so its calculations, errors, and source attribution are testable without an API key.

## Definition of done

- [ ] Known products return the correct quote, lead time, and source.
- [ ] Quantity drives total price deterministically.
- [ ] Zero, negative, boolean, and non-integer quantities are rejected.
- [ ] Missing/blank/non-string SKU values are rejected.
- [ ] Unknown SKUs produce a typed error.
- [ ] Output is JSON-serializable and includes every documented field.
- [ ] All tests pass offline.
