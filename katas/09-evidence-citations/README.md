# Kata 09 — Require Evidence and Citation Mapping

## Learning goal

Build a deterministic grounding layer that prevents unsupported procurement facts from appearing as if they came from a supplier quote or research source.

The kata stores source facts in stable `EvidenceRecord` objects and derives structured `Claim` objects only when evidence is present and unambiguous. Missing or conflicting evidence becomes an explicit uncertainty. A recommendation is marked as derived; it is not a source fact.

## Public API

```python
response = assemble_grounded_response(
    evidence=[
        EvidenceRecord("quote-13", "supplier catalog", {"total_usd": 27475, "lead_days": 7}),
    ],
    requested_fields=("total_usd", "lead_days", "memory_gb"),
    recommendation=DerivedRecommendation("approve", ("quote-13",)),
)
```

A response has:

- `claims`: observed facts with `field`, `value`, `evidence_id`, and `source`;
- `uncertainties`: structured missing/conflicting evidence states;
- `recommendation`: an optional derived conclusion with its supporting evidence IDs.

## Rules

1. A factual claim must point to exactly one stable evidence record.
2. Missing evidence never becomes a guessed claim.
3. Conflicting values become an uncertainty rather than a silent choice.
4. The response keeps facts and recommendations as different types.
5. Natural-language presentation can be generated later from this structure, but it is not tested here.

## Red → green → refactor progression

1. Map a price from one quote record to a cited claim.
2. Map lead time from the same record.
3. Make missing fields explicit uncertainties.
4. Detect conflicting values across sources.
5. Preserve evidence ID and source provenance.
6. Attach a derived recommendation separately from observed facts.
7. Serialize the result for a UI/activity log without producing prose.

## Run the kata

```powershell
python -m unittest discover -s katas/09-evidence-citations -p "test_*.py" -v
```

Set `KATA_MODULE=starter` to work through the intentionally incomplete scaffold.

## Definition of done

- [ ] Price and lead-time claims retain source/evidence IDs.
- [ ] Unsupported fields become uncertainties, not facts.
- [ ] Conflicting records do not create a fabricated winner.
- [ ] Derived recommendation remains separate from source facts.
- [ ] All output is deterministic and JSON-friendly.
- [ ] No network/model/API dependency exists.
