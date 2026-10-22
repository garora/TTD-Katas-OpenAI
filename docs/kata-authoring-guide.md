# Kata Authoring Guide

This guide defines the standard for adding a new TDD kata to this repository. A kata is a small, progressive exercise that teaches one engineering boundary or behavior at a time. It should be approachable without credentials, a live OpenAI request, or knowledge of future katas.

## Authoring principles

1. **One primary learning goal.** A kata may have several steps, but they should build one coherent skill.
2. **Start deterministic.** Teach validation, policy, state, orchestration, and tool contracts with fakes before introducing optional model calls.
3. **Make the contract observable.** Assert data shape, tool events, policy results, evidence, and state transitions—not a model’s exact prose.
4. **Use red → green → refactor.** Each step introduces one failing test and the smallest passing behavior.
5. **Keep the public API small.** Learners should quickly see the function/class they are meant to drive.
6. **Document error behavior.** Invalid input, tool failure, retry limits, uncertainty, and deferred work are part of the contract.
7. **Avoid secrets and live dependencies.** The default kata must run offline.

## Required kata anatomy

Create a numbered folder under `katas/`:

```text
katas/NN-short-name/
├── README.md       # Problem statement and learner instructions
├── starter.py      # Intentionally incomplete implementation
├── solution.py     # Reference implementation
└── test_kata.py    # Focused offline tests
```

Additional small fixture files are welcome when they materially improve the exercise. Do not add a dependency or provider SDK only for one kata unless the learning objective specifically requires it and setup remains clear.

### `README.md`

Every kata README must include:

- title and learning goal;
- why the skill matters for OpenAI/agent applications;
- explicit public API and input/output examples;
- prerequisites, if any;
- progressive red-green-refactor steps;
- offline command to run the test suite;
- error/failure behavior;
- definition-of-done checklist;
- a note explaining whether and how it connects to a later OpenAI adapter/live evaluation.

### `starter.py`

The starter implementation should:

- import only what learners need to begin;
- expose the intended public function/class and meaningful types/exceptions;
- have enough validation/scaffolding to clarify the first test;
- remain deliberately incomplete;
- contain concise TODOs rather than a hidden solution.

A checked-in repository should stay green. One simple pattern is for `test_kata.py` to default to `solution.py`, with an environment variable (such as `KATA_MODULE=starter`) allowing the learner to run the same tests against the starter.

### `solution.py`

The reference solution should:

- pass all kata tests;
- be readable and intentionally modest rather than overly abstract;
- validate untrusted inputs at the boundary;
- avoid API keys, network requests, and global mutable runtime state;
- demonstrate the design lesson in the README.

### `test_kata.py`

Tests should be ordered as a learner can implement the behavior. Each test should make one expectation clear.

Preferred tests assert:

- valid/invalid schema fields;
- tool name and validated argument shape;
- deterministic price/policy calculation;
- sequence/state transition;
- maximum loop/retry behavior;
- required evidence/citation;
- explicit uncertainty/deferred state;
- absence of unsupported/unsafe behavior.

Avoid tests that assert an exact model-generated sentence unless the code under test is a deterministic formatter.

## Standard public-contract checklist

Before writing code, define:

| Contract part | Questions to answer |
| --- | --- |
| Inputs | Which types, fields, ranges, IDs, and limits are accepted? |
| Outputs | What exact typed/JSON-serializable result does success return? |
| Errors | Which invalid states raise/return what error type and message? |
| Side effects | Does the kata write state, invoke a tool, or call a model? How is this faked? |
| Authority | Which component is allowed to decide policy or execute the action? |
| Evidence | Which result fields need a source/provenance ID? |
| Safety | What hostile/malformed input must remain harmless? |
| Test mode | What runs offline by default? What, if anything, is live opt-in? |

## Progressive-step template

Use this format in the README:

```markdown
1. **Red:** State one observable behavior.
   - **Green:** Implement the smallest code that passes it.
   - **Refactor:** Improve names/duplication while tests remain green.
```

Example:

```markdown
1. **Red:** A quote request for a known SKU returns a unit price.
   - **Green:** Look up one SKU in a local catalog.
   - **Refactor:** Introduce a `CatalogItem` type only if it clarifies the code.
2. **Red:** A quote quantity changes the total.
   - **Green:** Return `unit_price * quantity`.
   - **Refactor:** Keep calculation and validation separate.
```

Do not begin with a large multi-behavior test. Split each rule into its own small red-green step.

## Test-fixture guidance

Use fixtures when a kata needs representative events or adversarial content:

- synthetic/recorded normalized model events belong in `tests/fixtures/model-events/`;
- deterministic tool results belong in `tests/fixtures/tool-results/`;
- hostile/malformed inputs belong in `tests/fixtures/adversarial-prompts/`;
- reusable behavioral cases belong in `evals/datasets/`.

Fixtures must be minimal, redacted, and safe to commit. Never include credentials, customer data, or raw production context containing sensitive information.

## When to use a fake vs. a live model

Use a fake when testing logic your application owns: parsing, validation, tool dispatch, session state, policy, evidence tracking, and response assembly. A fake should expose the exact event/result sequence the kata needs.

Use an optional live evaluation only when the learning objective is specifically real model/configuration behavior. It must be separately invoked, credential-gated, cost-bounded, and paired with a stable offline evaluator wherever possible.

## Author checklist

Before opening a pull request or marking an issue complete:

- [ ] The kata has one clear primary learning goal.
- [ ] `README.md`, `starter.py`, `solution.py`, and `test_kata.py` exist.
- [ ] The public API, output shape, and error behavior are documented.
- [ ] Tests are offline, deterministic, and credential-free by default.
- [ ] Tests progress in small red-green-refactor steps.
- [ ] The starter is incomplete and does not reveal the solution.
- [ ] The reference solution passes all tests.
- [ ] The kata includes malformed/adversarial cases where it crosses a trust boundary.
- [ ] Exact LLM prose is not used as the main assertion.
- [ ] The README includes the exact local test command.
- [ ] No secrets, tokens, customer data, or live credentials are committed.
- [ ] A future relationship to tools, structured output, sessions, evaluation, or a later kata is explained when relevant.

## Copyable README skeleton

````markdown
# Kata NN — Short Name

## Learning goal
Explain the one behavior/boundary the learner will practice.

## Why it matters for OpenAI applications
Explain the production concern in practical terms.

## Public API
```python
function_or_type(...)
```

## Red → green → refactor progression
1. **Red:** …
   - **Green:** …
   - **Refactor:** …

## Run the kata
```powershell
python -m unittest discover -s katas/NN-short-name -p "test_*.py" -v
```

## Definition of done
- [ ] …
````

Use this skeleton as a starting point, then add examples and safety/error details relevant to the kata.
