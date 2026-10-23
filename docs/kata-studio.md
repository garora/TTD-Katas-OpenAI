# TDD Kata Studio

Kata Studio is one local dashboard for the entire curriculum, with a dedicated execution workspace per kata. It uses the Python standard library, local HTML/CSS/JavaScript, and a real `unittest` subprocess. There is no npm install, frontend build, CDN, telemetry, OpenAI SDK, API key, or model call.

## Quick start

Requires **Python 3.11 or later** (the existing typed kata contracts use `StrEnum`). Run from the repository root:

```powershell
python -m studio
```

Open **http://127.0.0.1:8765** in a current browser. If the port is occupied:

```powershell
python -m studio --port 8766
```

The service always binds to `127.0.0.1`; there is intentionally no public-host option. Stop it with **Ctrl+C** in the terminal.

## What is available?

Katas **01 — Prompt Builder**, **02 — Structured Output**, **03 — Supplier Quote Tool**, **04 — Tool Selection**, **05 — Tool Loop**, **06 — Budget Policy**, **07 — Session State**, and **08 — Prompt Injection** have implementations and real test suites. Katas **09–11** are visible as planned previews with disabled execution. Availability and last test outcome are different: a planned kata is never presented as passing.

The registry (`studio/katas.json`) contains the curriculum descriptions, conceptual stages, and the function names associated with those stages. Availability is derived from the presence of a kata's README, tests, starter, and solution—not hardcoded to a pass/fail badge. Adding those files makes a registered kata available on the next dashboard refresh.

## Use the workspace

1. Open an available kata from its card or the left navigation.
2. Choose **Reference solution** or **Starter (exercise)**.
3. Select **Run tests**. Real tests execute immediately in a fresh Python process.
4. The **Test explorer** shows each actual test's outcome, including assertion failures, errors, skips, and failing subtests.
5. The **Execution map** shows conceptual stages and badges for observed function calls.
6. Select a test or an event in the **Event timeline** to inspect the outcome, source file/line, function name, return type, or failure details.
7. Open **Kata instructions** for the kata's checked-in README (displayed as safe plain text).
8. Use **Run history** to reopen a saved run, including a run that is still active.

The starters are intentionally incomplete: failures/errors are expected. A reference solution should be green. This is not a scoring service or proof that a learner used TDD.

### Practice with your own working copy

Keep the reference implementation intact. Create a local working module:

```powershell
Copy-Item katas/03-supplier-quote-tool/starter.py katas/03-supplier-quote-tool/working.py
```

On macOS/Linux:

```bash
cp katas/03-supplier-quote-tool/starter.py katas/03-supplier-quote-tool/working.py
```

Refresh the Studio page and open that kata again. **Working copy** now appears in the target selector. Edit `working.py` in your IDE, run the tests, and iterate. Working copies are ignored by Git by default. Studio does not edit source code.

## Live reporting and replay

The server sends captured events over **Server-Sent Events (SSE)** as the worker produces them. Test execution is not artificially slowed for animation. Small test suites may finish too quickly to watch live; replay is the teaching mode for those cases.

After a run ends:

- **Replay** plays through recorded events without running tests again.
- **Step** advances one event at a time; move the slider to an earlier position first if already at the end.
- The **event slider** reconstructs the visible test outcomes and observed-function counts at that point.
- **Run history** reopens persisted events after a server restart.

SSE reconnects use event sequence IDs to resume without duplicating events or re-executing tests. Leaving a workspace does not cancel or retry an active run. Reopen it from Run history. Only one run may execute at a time; overlap is rejected by the backend as well as disabled in the UI.

### What the diagrams do—and do not—mean

- The connected stages show a **conceptual teaching order**, not an observed dependency/call graph.
- A call-count badge is based on a real Python trace event from the selected target module.
- Only function names listed in the registry are traced. No events are fabricated for uninstrumented stages.
- Trace events include function name, test ID, line, action (`call`/`return`), and return **type**; they do not include argument values, return values, or local variables.
- A Python `return` trace may also arise during exception unwinding; it does not prove successful completion. Test verdicts are authoritative for pass/fail.
- A passing test run proves only the tested behavior. Studio cannot certify that a learner performed red–green–refactor or that code is secure.

## Storage and runtime limits

Local event logs are saved as `.studio-state/runs/<run-id>.jsonl`. This directory is ignored by Git. The first event also records the visual-stage mapping and SHA-256 fingerprints of the selected target and test module, so replay is identifiable even after edits. Source text is not snapshotted. Each event has an ordered sequence ID and UTC timestamp; UI dates use the browser's local timezone.

Defaults:

- one active run across the server; an OS-backed lock prevents two Studio servers from writing the same checkout history;
- 30-second worker timeout;
- 1–250 test cases per suite;
- at most 1,500 function-trace events (test reporting continues after the trace limit);
- bounded event/error payloads;
- unfinished saved runs become **interrupted** on restart, without automatic replay.

Stop Studio before deleting local history. History is deliberately local and not shared with GitHub. It is not automatically pruned; remove `.studio-state` when you no longer need the records. Avoid keeping large numbers of runs indefinitely.

## Safety and privacy

- Run only trusted repository code. A Python subprocess plus audit hooks is **not a security sandbox**.
- The server accepts only registered kata IDs and fixed `starter`, `solution`, or `working` targets. Browser requests cannot supply shell commands or arbitrary file paths.
- The HTTP API validates loopback Host headers and same-origin run requests, does not enable CORS, and exposes only allow-listed static assets.
- Workers use a reduced environment: application/API credentials are not forwarded. The existing kata suites require no secrets.
- Worker audit hooks reject ordinary Python socket connections, DNS resolution, and child-process execution. These are defense in depth, not a guarantee against malicious Python/native code.
- The worker deliberately omits argument/return values and local variables from traces. Common credential-shaped error strings are redacted.
- Assertion errors may still contain test-authored text, source lines, or local filesystem paths. Redaction is best-effort, not exhaustive. Never put credentials or customer data in exercise files, fixtures, or assertion messages.
- Browser content is rendered as text, not untrusted HTML. Frontend assets are served locally with a restrictive content-security policy.
- Studio is a single-user local learning tool—not an authenticated multi-user or internet-facing service. Do not expose it through public tunnels or reverse proxies.

## Test everything offline

```powershell
python -B scripts/run_tests.py
```

This runs existing package tests, Studio tests, and all available kata reference suites in **separate Python interpreters**, avoiding collisions between the kata-local `solution` and `test_kata` modules. It clears inherited `KATA_MODULE` for reference-suite validation. Starter failures are checked deliberately inside the Studio test suite.

For just Studio's regression tests:

```powershell
python -B -m unittest discover -s tests/studio -p "test_*.py" -v
```

Tests cover real worker runs, all three reference solutions and intentionally failing starters, function traces, durable replay, restart recovery, timeouts, overlap rejection, credential-environment isolation, network blocking, HTTP restrictions, live SSE before completion, and resume by event ID. Tests make loopback HTTP requests only; they do not contact OpenAI.

## Extend Studio with the next kata

When completing an additional kata:

1. Add its README, starter, solution, and tests using [the authoring guide](kata-authoring-guide.md).
2. Keep test imports compatible with `KATA_MODULE=starter|solution|working`. Run each kata in its own process.
3. Update the kata's entry in `studio/katas.json`: describe the conceptual stages and list exact implementation function names for trace association.
4. Leave a function list empty for any conceptual stage that has no capture hook. Do not pretend an event exists.
5. Verify a green reference run, an intentionally red starter run, and correct observed-stage badges in Studio.
6. Run `python -B scripts/run_tests.py` and add regressions for new event shapes or boundary behavior.
7. Update the root README's availability section when the curriculum changes.

This is the maintenance convention for future work, not an autonomous background automation. Studio is ready to discover newly completed registered katas without adding a separate frontend application for each one.

## Implementation map

```text
studio/
├── __main__.py       # CLI: python -m studio
├── registry.py       # Curriculum lookup and allow-listed targets
├── katas.json        # Descriptions, conceptual stages, trace function names
├── worker.py         # Isolated unittest lifecycle + targeted Python traces
├── runner.py         # Subprocess bounds, durable event logs, restart recovery
├── server.py         # Loopback HTTP API, origin controls, SSE
└── web/              # Local HTML, CSS, JavaScript; no build step
scripts/run_tests.py  # Offline regression entry point
```

## Troubleshooting

| Symptom | Action |
| --- | --- |
| `Studio is already using this checkout` | Stop the other Studio server before starting another port for the same checkout. The history lock is released when its process exits. |
| `Address already in use` | Start with another `--port`. |
| `No module named studio` | Run the command from this repository's root directory. |
| Starter run is red | Expected: implement the exercise in `working.py`, then select Working copy. |
| No observed badges | Inspect the test result first. Verify the target actually called a function named in the registry. No capture means “not observed,” not “passed.” |
| Working copy missing from selector | Create `working.py` beside the kata starter and reopen the workspace after refresh. |
| Run is interrupted/timed out | Inspect its saved events and fix the cause before explicitly starting a new run. Studio never silently retries. |
| Stream disconnected | Leave the server running and reopen Run history. Event IDs permit resuming; do not repeatedly click Run. |
