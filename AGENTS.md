# Repository contributor instructions

## Offline-first defaults

- Keep all default kata and package tests credential-free and offline. Do not add live OpenAI calls to the default runner.
- Do not commit credentials, local `.env` files, `.studio-state/`, Python caches, generated reports, or learner working copies.
- Run `python -B scripts/run_tests.py` from the repository root before completing a code change. This isolates same-named kata modules in separate interpreters.

## Completing or changing a kata

- Follow `docs/kata-authoring-guide.md` for README, starter, solution, tests, and red-green-refactor steps.
- Keep kata tests compatible with `KATA_MODULE=starter|solution|working`.
- Update the corresponding entry in `studio/katas.json` whenever behavior/function names change: descriptions, conceptual stages, and exact trace function names must remain accurate.
- Verify the reference solution passes, the starter fails as intended, and Studio reports captured events honestly. Extend Studio regression coverage when introducing a new reporting behavior.
- Update the root README's availability summary when a registered kata becomes runnable.
- Never fabricate execution events or treat a conceptual diagram as an observed call graph. A passing run does not prove TDD/refactoring or security.

## Studio safety and scope

- Studio is a single-user loopback-only service for trusted code, not a sandbox or internet-facing service.
- Preserve the fixed target allow-list, Host/Origin checks, bounded subprocesses, reduced worker environment, and replay-without-execution behavior.
- Do not capture argument values, return values, local variables, credentials, or customer data in trace events.
- See `docs/kata-studio.md` for startup, storage, extension, event semantics, and limitations.
