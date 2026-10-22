"""One isolated unittest process. Emits JSON, never provider/API requests."""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import sys
import time
import traceback
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from studio.registry import ROOT, validate_target

MAX_TRACE_EVENTS = 1500


def scrub(text: object) -> str:
    value = str(text)
    value = re.sub(r"(?i)(?:sk-(?:proj-)?[\w-]{12,}|gh[pousr]_[\w]{15,}|github_pat_[\w_]{15,})", "[REDACTED]", value)
    value = re.sub(r"(?i)((?:password|api[_-]?key|access[_-]?token|secret)\s*[:=]\s*)[^\s,}]+", r"\1[REDACTED]", value)
    return value[:3500]


def emit(kind: str, **values: object) -> None:
    print(json.dumps({"kind": kind, **values}, ensure_ascii=True), flush=True)


def block_external_actions(event: str, args: tuple) -> None:
    # Defense in depth for trusted local exercise code, NOT a Python sandbox.
    if event in {"socket.connect", "socket.connect_ex", "socket.getaddrinfo", "socket.bind",
                 "subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn"}:
        raise PermissionError("Studio workers do not permit network or child-process actions")


class ReportingResult(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.current = None
        self.verdict = "passed"
        self.details = ""
        self.started = 0.0
        self.counts = {name: 0 for name in ("passed", "failed", "error", "skipped", "expected_failure")}
        self.trace_count = 0

    def startTest(self, test):
        super().startTest(test)
        self.current = test.id()
        self.verdict, self.details = "passed", ""
        self.started = time.monotonic()
        emit("test_started", test_id=self.current, label=test._testMethodName)

    def problem(self, status, err):
        self.verdict = status
        self.details = scrub("".join(traceback.format_exception(*err)))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.problem("failed", err)

    def addError(self, test, err):
        super().addError(test, err)
        self.problem("error", err)

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self.problem("failed" if issubclass(err[0], test.failureException) else "error", err)

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.verdict, self.details = "skipped", scrub(reason)

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.verdict = "expected_failure"

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.verdict, self.details = "failed", "Unexpected success of an expected-failure test"

    def stopTest(self, test):
        self.counts[self.verdict] += 1
        emit("test_finished", test_id=test.id(), status=self.verdict,
             duration_ms=round((time.monotonic() - self.started) * 1000, 3), details=self.details)
        self.current = None
        super().stopTest(test)


def main() -> int:
    root, kata_id, target = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    kata = validate_target(kata_id, target, root)
    folder = (root / "katas" / kata_id).resolve()
    implementation = (folder / f"{target}.py").resolve()
    os.environ["KATA_MODULE"] = target
    sys.path.insert(0, str(folder))
    sys.dont_write_bytecode = True
    sys.addaudithook(block_external_actions)
    result = ReportingResult()
    function_stages = {name: stage["id"] for stage in kata["stages"] for name in stage.get("functions", [])}

    def trace(frame, event, arg):
        if (result.current and event in {"call", "return"}
                and frame.f_code.co_filename == str(implementation)):
            name = frame.f_code.co_name
            if name in function_stages and result.trace_count < MAX_TRACE_EVENTS:
                result.trace_count += 1
                emit("trace", test_id=result.current, stage=function_stages[name],
                     function=name, action=event, line=frame.f_lineno,
                     file=f"katas/{kata_id}/{target}.py",
                     result_type=type(arg).__name__ if event == "return" else None)
                if result.trace_count == MAX_TRACE_EVENTS:
                    emit("notice", message="Trace limit reached; test reporting continues without further trace events.")
        return trace

    emit("worker_started", target=target, trace="function calls/returns; values and locals not captured")
    try:
        suite = unittest.defaultTestLoader.discover(str(folder), pattern="test_*.py")
        total = suite.countTestCases()
        emit("suite_loaded", total=total)
        if total == 0 or total > 250:
            raise ValueError("A Studio suite must contain 1–250 tests")
        sys.settrace(trace)
        suite.run(result)
    finally:
        sys.settrace(None)
    emit("suite_finished", counts=result.counts, total=result.testsRun,
         status="passed" if result.wasSuccessful() else "failed")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    try:
        exit_code = main()
    except Exception as exc:
        emit("worker_error", error_type=type(exc).__name__, message=scrub(exc))
        exit_code = 2
    raise SystemExit(exit_code)
