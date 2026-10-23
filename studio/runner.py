"""Bounded subprocess execution with durable append-only run events."""
from __future__ import annotations
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import threading
import uuid
from datetime import datetime, timezone

from .registry import ROOT, validate_target


class BusyError(RuntimeError):
    pass


class RunManager:
    def __init__(self, root: Path = ROOT, state_dir: Path | None = None, timeout: float = 30):
        self.root = root.resolve()
        self.state_dir = (state_dir or self.root / ".studio-state" / "runs").resolve()
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.condition = threading.Condition(threading.RLock())
        self.runs: dict[str, list[dict]] = {}
        self.active = None
        self.process = None
        self.closing = False
        self._recover()

    def _recover(self):
        for path in sorted(self.state_dir.glob("*.jsonl")):
            try:
                uuid.UUID(path.stem)
                lines = path.read_text(encoding="utf-8").splitlines()
                events = []
                for index, line in enumerate(lines):
                    try:
                        event = json.loads(line)
                    except ValueError:
                        if index != len(lines) - 1:
                            raise
                        # A crash can interrupt the last append. Preserve prior events.
                        path.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
                        break
                    if not isinstance(event, dict) or event.get("seq") != len(events) + 1:
                        raise ValueError("Invalid saved event sequence")
                    events.append(event)
                if not events or events[0].get("kind") != "run_started":
                    continue
                self.runs[path.stem] = events
                if events[-1]["kind"] != "run_finished":
                    self.append(path.stem, "run_finished", status="interrupted",
                                reason="Studio restarted; no tests were automatically replayed")
            except (ValueError, OSError, KeyError):
                continue

    def append(self, run_id, kind, **data):
        with self.condition:
            events = self.runs[run_id]
            event = {**data, "kind": kind, "seq": len(events) + 1,
                     "at": datetime.now(timezone.utc).isoformat(), "run_id": run_id}
            with (self.state_dir / f"{run_id}.jsonl").open("a", encoding="utf-8") as file:
                file.write(json.dumps(event, ensure_ascii=True) + "\n")
            events.append(event)
            self.condition.notify_all()
            return event

    def start(self, kata_id, target):
        kata = validate_target(kata_id, target, self.root)
        folder = self.root / "katas" / kata_id
        hashes = {name: hashlib.sha256((folder / name).read_bytes()).hexdigest()
                  for name in (f"{target}.py", "test_kata.py")}
        with self.condition:
            if self.active or self.closing:
                raise BusyError("A test run is already active; wait for it to finish")
            run_id = str(uuid.uuid4())
            self.runs[run_id] = []
            self.active = run_id
            self.append(run_id, "run_started", kata_id=kata_id, target=target, stages=kata["stages"], source_hashes=hashes)
            threading.Thread(target=self._execute, args=(run_id, kata_id, target), daemon=True).start()
            return run_id

    def _execute(self, run_id, kata_id, target):
        status, reason = "error", "Worker did not finish"
        # Do not forward credentials or arbitrary user Python configuration.
        environment = {key: os.environ[key] for key in
                       ("SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "LANG") if key in os.environ}
        process = None
        reader = None
        try:
            worker = Path(__file__).with_name("worker.py")
            flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            process = subprocess.Popen(
                [sys.executable, "-I", "-B", "-u", str(worker), str(self.root), kata_id, target],
                cwd=self.root, env=environment, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8",
                errors="replace", creationflags=flags,
            )
            with self.condition:
                self.process = process
                if self.closing:
                    process.kill()

            def read_events():
                for line in iter(lambda: process.stdout.readline(16001), ""):
                    try:
                        payload = json.loads(line)
                        kind = payload.pop("kind")
                        if kind not in {"worker_started", "test_started", "test_finished", "trace",
                                        "suite_loaded", "suite_finished", "worker_error", "notice"}:
                            continue
                        # Worker payloads are already bounded and do not contain locals.
                        if len(line) <= 16000 and len(self.runs[run_id]) < 5000:
                            self.append(run_id, kind, **payload)
                    except (ValueError, KeyError, TypeError):
                        # Arbitrary test print output isn't a structured event or persisted.
                        continue

            reader = threading.Thread(target=read_events, daemon=True)
            reader.start()
            try:
                process.wait(timeout=self.timeout)
                reason = ""
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                status, reason = "timed_out", f"Run exceeded {self.timeout:g} second limit"
            reader.join(timeout=5)
            if not reason:
                finished = next((e for e in reversed(self.runs[run_id]) if e["kind"] == "suite_finished"), None)
                status = finished["status"] if finished and process.returncode in (0, 1) else "error"
                if status == "error":
                    reason = "Worker exited without a valid test summary; inspect recorded events"
        except Exception as exc:
            reason = f"Runner error: {type(exc).__name__}"
        finally:
            if process and process.poll() is None:
                process.kill()
                process.wait()
            if reader:
                reader.join(timeout=5)
            if process and process.stdout:
                process.stdout.close()
            with self.condition:
                if self.closing:
                    status, reason = "interrupted", "Studio stopped; no automatic retry"
                self.append(run_id, "run_finished", status=status, reason=reason)
                self.active, self.process = None, None
                self.condition.notify_all()

    def events(self, run_id, after=0):
        with self.condition:
            if run_id not in self.runs:
                raise KeyError("Unknown run")
            return list(self.runs[run_id][after:])

    def history(self):
        with self.condition:
            history = []
            for run_id, events in self.runs.items():
                first, last = events[0], events[-1]
                summary = next((e for e in reversed(events) if e["kind"] == "suite_finished"), {})
                history.append({"id": run_id, "kata_id": first["kata_id"], "target": first["target"],
                                "started_at": first["at"], "counts": summary.get("counts", {}),
                                "status": last["status"] if last["kind"] == "run_finished" else "running"})
            return sorted(history, key=lambda run: run["started_at"], reverse=True)

    def close(self):
        with self.condition:
            self.closing = True
            if self.process and self.process.poll() is None:
                self.process.kill()
            self.condition.wait_for(lambda: self.active is None, timeout=10)
