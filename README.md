# TDD Katas for OpenAI

A progressive set of **test-driven development (TDD) exercises for AI applications**. These katas use the familiar **red → green → refactor** loop while teaching the additional engineering practices needed for OpenAI-powered systems: structured output, tool calling, stateful sessions, evaluation datasets, grounding, and safety.

> **Core rule:** Test observable contracts—not the exact wording of an LLM response.

## TDD Kata Studio — visualize the tests

A shared local dashboard is now available, with an individual visual workspace for every kata. **All 11 katas are implemented and runnable in the shared Studio.** Availability is separate from test status; planned exercises are never shown as passing.

### Start the dashboard

Requires **Python 3.11+** and a current browser. In a terminal at this repository's root:

```powershell
python -m studio
```

Open **http://127.0.0.1:8765**. If that port is busy, run `python -m studio --port 8766` instead. No package install, npm, frontend build, API key, or OpenAI request is needed. Stop the server with **Ctrl+C**.

### Explore a kata

1. Open an available kata from the dashboard or left navigation.
2. Select **Reference solution** or **Starter (exercise)** and click **Run tests**.
3. See every statically discovered kata test in the **Test explorer** before execution, then follow genuine live `unittest` results and recorded function events in the **Event timeline**.
4. Select an event to inspect its test, source location, outcome, return type, or failure details.
5. Use **Kata instructions** to read the exercise without leaving the workspace.
6. After the run finishes, choose **Replay**, **Step**, or the event slider to understand what happened. Replay reads saved events; it does not execute tests again. Its visual state is **green** for passed, **amber** for mixed, and **red** for failed, timed-out, or interrupted snapshots.
7. Read **Run guidance** for the first actionable failed test, a concise sanitized reason, and the next suggested step. Starter failures are intentionally red and direct learners to a Working copy.
8. Reopen any previous run from **Run history**. Browser disconnection does not automatically retry or cancel a run.

The execution map is a **conceptual teaching diagram**, not a captured call graph. Its observed-function badges come from genuine Python trace events. Stages with no trace remain labelled as unobserved. Arguments, return values, and local variables are not captured. A passing run does not prove that someone followed TDD or refactored correctly.

### Practice without changing the solution

Create a local working copy, for example:

```powershell
Copy-Item katas/03-supplier-quote-tool/starter.py katas/03-supplier-quote-tool/working.py
```

On macOS/Linux, use `cp` instead of `Copy-Item`. Refresh the page and reopen the kata; **Working copy** appears in the target selector. Edit the file in your IDE and rerun the tests. Working copies are ignored by Git. The incomplete starters are expected to produce red results; the references should pass.

### Run all offline checks

```powershell
python -B scripts/run_tests.py
```

This runs package, Studio, and all 11 reference-kata suites in separate interpreters, preventing collisions between same-named kata modules. Studio tests also verify real failing starter runs, timeouts, replay persistence, live event delivery, and request restrictions. They make loopback HTTP requests only—not OpenAI calls.

### Local data and safety

- Run events are stored in **`.studio-state/runs/`**, ignored by Git. Stop Studio before deleting local history. History is not automatically pruned.
- One run at a time, a 30-second worker timeout, bounded event payloads, and a function-trace limit keep the learning runner bounded.
- The server binds only to `127.0.0.1`, checks Host/Origin headers, and accepts registered kata IDs and fixed targets—not arbitrary commands or paths.
- Workers receive a reduced environment without application/API credentials; audit hooks block ordinary Python network and child-process actions.
- **This is not a security sandbox.** Execute only trusted repository code. Do not expose Studio publicly or place secrets/customer data in exercises or assertions. Error redaction is best-effort; failures can contain test-authored text and local paths.

### Keep Studio aligned with future katas

`studio/katas.json` is the shared curriculum/visual-stage registry. A registered kata becomes runnable when its README, tests, starter, and solution exist. Whenever completing another kata, update its stage/function mapping, verify its reference and starter runs in Studio, run the offline suite, and update the documented availability. This is a contributor convention, not an unattended background automation.

See **[the full Studio guide](docs/kata-studio.md)** for storage, event semantics, implementation details, extension steps, and troubleshooting.

## Why AI TDD is different

Traditional kata tests normally assert one deterministic return value. Model output can vary even when the application behaves correctly, so these katas focus on stable invariants:

- The expected tool is called with validated arguments.
- Structured output conforms to a schema.
- Business rules are decided in deterministic code.
- Answers only claim facts supported by supplied evidence.
- Unsafe or malformed requests fail safely.
- Agent/session orchestration preserves the intended state and boundaries.

## Learning path

| # | Kata | Main skill | Suggested contract to test |
| --- | --- | --- | --- |
| 01 | Prompt Builder | Prompt composition and instruction boundaries | Required instructions are present; untrusted content cannot replace system policy. |
| 02 | Structured Output | Schema-first model integration | Valid output parses; invalid or incomplete output is rejected or repaired. |
| 03 | Supplier Quote Tool | Deterministic function tools | Inputs validate; quote totals, lead time, and provenance are correct. |
| 04 | Tool Selection | Choosing a tool vs. clarifying | Complete quote requests create a quote tool call; ambiguous requests ask a question. |
| 05 | Tool Loop | Agent orchestration | Tool results return to the model; limits prevent loops; unknown calls fail safely. |
| 06 | Budget Policy | Deterministic decision logic | Quotes over budget or deadline are rejected without an LLM deciding policy. |
| 07 | Session State | Conversation/session lifecycle | Follow-up turns reuse one session; fresh chats create distinct sessions. |
| 08 | Prompt Injection | Untrusted-data handling | Retrieved/tool text cannot alter permissions, policy, or reveal secrets. |
| 09 | Evidence & Citations | Grounded responses | Price/deadline claims map to tool or retrieval evidence. |
| 10 | Multi-Agent Delegation | Handoffs and aggregation | Children receive the necessary facts; parent records failed/deferred work honestly. |
| 11 | Evaluation Dataset | Regression protection | Fixtures exercise tools, schemas, grounding, safety, latency, and cost thresholds. |

## The TDD loop

For each small step:

1. **Red** — Write one failing test that expresses a single behavior.
2. **Green** — Write only enough production code to make it pass.
3. **Refactor** — Improve names, duplication, and boundaries while tests remain green.
4. **Regress** — Preserve the new case in an offline fixture or evaluation dataset.

Start from deterministic components—validation, policy, tool functions, and session storage—then add the model adapter and finally optional live evaluations.

## Repository structure

```text
TDD-Katas-OpenAI/
├── README.md                         # Curriculum, setup, and kata index
├── AGENTS.md                         # Contributor instructions and Studio conventions
├── studio/                           # Local dashboard, runner, SSE, and visual registry
│   ├── katas.json                    # Curriculum stages and trace mappings
│   └── web/                          # Dependency-free browser UI
├── docs/
│   ├── architecture.md                # Boundaries: model, tools, policy, storage
│   ├── testing-strategy.md            # Offline, contract, and live-eval guidance
│   ├── kata-authoring-guide.md        # Standard for adding a kata
│   └── kata-studio.md                 # Studio usage, replay, safety, and extension guide
├── katas/
│   ├── 01-prompt-builder/ ... 11-evaluation-dataset/
│   │   ├── README.md                  # Problem statement and progression
│   │   ├── starter.py                 # Deliberately incomplete learner code
│   │   ├── solution.py                # Reference implementation
│   │   └── test_kata.py               # Offline kata contract tests
├── src/openai_tdd_katas/             # Reusable typed/domain, policy, tool, and orchestration code
├── tests/
│   ├── unit/                          # Fast reusable-package tests
│   ├── studio/                        # Loopback/subprocess Studio regressions
│   └── fixtures/                      # Synthetic model, tool, and adversarial data
├── evals/
│   ├── datasets/core_cases.jsonl      # Versioned offline evaluation cases
│   ├── graders/                       # Extension point for reusable graders
│   └── runner.py                      # Deterministic JSONL loader and invariant grader
├── scripts/run_tests.py               # Runs all offline suites in isolated interpreters
├── .gitignore                         # Excludes local runs, working copies, caches, and secrets
└── LICENSE.txt
```

## Documentation

The repository documentation describes the boundaries and conventions used by every kata:

- [Kata Studio](docs/kata-studio.md) — start the dashboard, run/replay tests, and extend the visual curriculum.
- [Architecture](docs/architecture.md) — model, tools, policy, sessions/storage, evidence, and trust boundaries.
- [Testing strategy](docs/testing-strategy.md) — offline unit/contract/integration tests, datasets, and opt-in live evaluations.
- [Kata authoring guide](docs/kata-authoring-guide.md) — the standard for adding a progressive exercise.
## Testing layers

### 1. Unit tests — always run

No network, no API key, no real model. Test pure policy, validation, transformation, and tool implementation.

```python
def test_quote_rejects_non_positive_quantity(self):
    with self.assertRaises(ValueError):
        get_supplier_quote({"sku": "workshop-13", "quantity": 0})
```

### 2. Contract/integration tests — use fakes

Use a fake model client that returns recorded response events. Assert the orchestration contract: selected tools, supplied arguments, schema parsing, tool-result handoff, maximum iteration count, and terminal state.

```python
def test_quote_request_invokes_quote_tool(agent, fake_model):
    fake_model.return_tool_call(
        name="get_supplier_quote",
        arguments={"sku": "workshop-13", "quantity": 25},
    )

    result = agent.run("Quote 25 workshop-13 laptops.")

    assert result.tool_calls[0].name == "get_supplier_quote"
```

### 3. Live evaluation tests — explicit and limited

Run these only with an authorized API key and a deliberate command. Use a small, versioned dataset and measure schema validity, tool-call correctness, evidence coverage, latency, and cost. Do not make ordinary CI depend on a live model response.

## Design rules

1. **Keep policy in code.** Budget limits, permissions, and authorization should be deterministic.
2. **Validate every boundary.** Validate user input, tool input, tool output, and model-produced structured data.
3. **Make tools small and observable.** Each tool should have narrow inputs, typed outputs, clear errors, and a unit-test suite.
4. **Treat external text as data.** Tool results, retrieval chunks, and documents are untrusted content—not instructions.
5. **Test invariants, not prose.** Assert schema, evidence, safety constraints, and tool events rather than an exact sentence.
6. **Separate offline and live testing.** The default test suite must be fast, inexpensive, repeatable, and credential-free.
7. **Add a regression fixture for every defect.** A production failure becomes a local test case and, when relevant, an evaluation example.
