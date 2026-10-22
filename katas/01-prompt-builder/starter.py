"""Starter implementation for Kata 01: Build a Secure Prompt Builder.

Work through test_kata.py one test at a time. This file intentionally leaves
important behavior unfinished; `solution.py` contains the reference solution.
"""


def build_instructions(
    role: str,
    *,
    policy: str | None = None,
    output_format: str | None = None,
    untrusted_content: str | None = None,
) -> str:
    """Build a trusted instruction envelope.

    Requirements to discover through the tests:
    - role is required and cannot be blank;
    - blank optional trusted sections are omitted;
    - untrusted content is data, not instruction text;
    - trusted sections always appear before untrusted content.
    """
    if not isinstance(role, str) or not role.strip():
        raise ValueError("role must be a non-blank string")

    # TODO: Add deterministic trusted sections for policy and output format.
    # TODO: Render untrusted content in a separate, JSON-encoded data envelope.
    return f"## System role\n{role.strip()}"
