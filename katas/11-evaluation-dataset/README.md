# Kata 11 — Create a Reusable Evaluation Dataset and Graders

## Learning goal

Turn earlier behaviors, failures, and safety boundaries into versioned regression cases. This final kata makes evaluation a deterministic offline loop: load cases, grade observable invariants, produce a concise report, and add a new case whenever a defect is fixed.

The default evaluation runner does not call a model or network. A future live evaluation must be explicit, credential-gated, cost-bounded, and separate from the default suite.

## Dataset format

Cases live in `evals/datasets/core_cases.jsonl`, one JSON object per line:

```json
{
  "id": "tool-selection-complete",
  "category": "tool_selection",
  "input": "Quote 25 workshop-13 laptops.",
  "expected": {
    "required_tool": "get_supplier_quote",
    "tool_arguments": {"sku": "workshop-13", "quantity": 25}
  }
}
```

Inputs are included for learner context. Reports deliberately do **not** echo raw input; a production evaluation dataset may contain sensitive material.

## Deterministic invariant types

| Expected key | Actual field checked |
| --- | --- |
| `required_tool` | `tool_name` |
| `tool_arguments` | subset of `tool_arguments` |
| `schema_valid` | `schema_valid` boolean |
| `decision` | `decision` |
| `required_evidence_ids` | `evidence_ids` set inclusion |
| `forbidden_terms` | lower-cased `text` exclusion |
| `requires_clarification` | `requires_clarification` boolean |
| `max_tool_steps` | `tool_steps` upper bound |

## Red → green → refactor progression

1. Load JSONL cases with ID/category/expected validation.
2. Grade a passing tool-selection case.
3. Report missing actual output without repeating the input text.
4. Add graders for schemas, policy decisions, evidence, safety, clarification, and loop limits.
5. Produce a report with per-case outcomes and aggregate counts.
6. Add a regression case for each new production-worthy defect.

## Run

```powershell
python -m unittest discover -s katas/11-evaluation-dataset -p "test_*.py" -v
```

The reusable runner is also importable:

```powershell
python -m evals.runner evals/datasets/core_cases.jsonl
```

The command expects actual results only when used from code; the CLI reports loaded-case metadata and does not run a live model.

## Adding a regression case

1. Reduce the bug to a safe, minimal input.
2. Add a JSONL case with a unique stable ID and one category.
3. State only observable expected invariants.
4. Add/update a deterministic grader if needed.
5. Add an offline test that demonstrates the prior failure and fixed behavior.
6. Never commit credentials, production prompts, customer data, or raw private tool results.

## Future live evaluations

A live path must be a deliberate separate command, require an authorized key, use a fixed small dataset, record cost/latency, set timeouts, and never be the only regression protection. It is intentionally not implemented in this kata.

## Definition of done

- [ ] JSONL cases have stable unique IDs, categories, inputs, and expected invariants.
- [ ] Deterministic graders cover tool calls, schemas, policy, evidence, safety, clarification, and loop limits.
- [ ] Reports include per-case pass/fail outcomes and aggregate counts without echoing raw input.
- [ ] Missing/invalid actual results fail with useful, non-sensitive diagnostics.
- [ ] The default runner is fully offline; any future live path remains explicit and opt-in.
- [ ] A regression case and offline test accompany each newly discovered defect.
