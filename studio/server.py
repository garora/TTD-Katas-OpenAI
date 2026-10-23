"""Loopback-only HTTP API and SSE delivery for Kata Studio."""
from __future__ import annotations
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

from .registry import ROOT, get_kata, load_katas
from .runner import BusyError, RunManager

ASSETS = Path(__file__).with_name("web")


class StateLock:
    """Prevent two server processes from recovering/writing the same run logs."""
    def __init__(self, state_dir):
        state_dir.mkdir(parents=True, exist_ok=True)
        self.file = (state_dir / ".server.lock").open("a+b")
        try:
            self.file.seek(0, 2)
            if self.file.tell() == 0:
                self.file.write(b"0")
                self.file.flush()
            self.file.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.file.close()
            raise RuntimeError("Studio is already using this checkout's run history; stop the other server first") from exc

    def close(self):
        # Closing the descriptor releases the OS lock, even after an unclean exit.
        self.file.close()


def create_server(port=8765, root: Path = ROOT, state_dir=None, timeout=30):
    state_dir = Path(state_dir or root / ".studio-state" / "runs").resolve()
    ownership = StateLock(state_dir)
    manager = None  # Acquire history ownership before any restart recovery.

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *_):
            pass  # Do not log request bodies, headers, or source content.

        def authorized(self, mutation=False):
            host = self.headers.get("Host", "")
            allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            if host not in allowed:
                self.send_json(403, {"error": "Only loopback Host headers are permitted"})
                return False
            origin = self.headers.get("Origin")
            if origin and origin not in {f"http://{value}" for value in allowed}:
                self.send_json(403, {"error": "Cross-origin requests are not permitted"})
                return False
            if mutation and origin != f"http://{host}":
                self.send_json(403, {"error": "Run requests require the same-origin browser"})
                return False
            return True

        def send_studio_headers(self, status, mime, length=None):
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
            if length is not None:
                self.send_header("Content-Length", str(length))
            self.end_headers()

        def send_json(self, status, data):
            encoded = json.dumps(data, ensure_ascii=True).encode("utf-8")
            self.send_studio_headers(status, "application/json; charset=utf-8", len(encoded))
            self.wfile.write(encoded)

        def do_GET(self):
            if not self.authorized():
                return
            parsed = urlsplit(self.path)
            path = parsed.path
            if path in {"/", "/app.js", "/styles.css"}:
                filename = {"/": "index.html", "/app.js": "app.js", "/styles.css": "styles.css"}[path]
                mime = {"/": "text/html", "/app.js": "text/javascript", "/styles.css": "text/css"}[path]
                content = (ASSETS / filename).read_bytes()
                self.send_studio_headers(200, mime + "; charset=utf-8", len(content))
                self.wfile.write(content)
                return
            if path == "/api/katas":
                self.send_json(200, {"katas": load_katas(root), "active_run": manager.active})
                return
            if path == "/api/runs":
                self.send_json(200, {"runs": manager.history(), "active_run": manager.active})
                return
            if path.startswith("/api/katas/"):
                try:
                    kata = get_kata(path.removeprefix("/api/katas/"), root)
                    guide = root / "katas" / kata["id"] / "README.md"
                    self.send_json(200, {**kata, "guide": guide.read_text(encoding="utf-8-sig") if guide.exists() else "This kata is planned. No runnable test suite is published yet."})
                except ValueError:
                    self.send_json(404, {"error": "Unknown kata"})
                return
            parts = path.strip("/").split("/")
            if len(parts) in (3, 4) and parts[:2] == ["api", "runs"]:
                run_id = parts[2]
                try:
                    if len(parts) == 3:
                        self.send_json(200, {"events": manager.events(run_id)})
                    elif parts[3] == "events":
                        after = int(self.headers.get("Last-Event-ID") or parse_qs(parsed.query).get("after", ["0"])[0])
                        if after < 0:
                            raise ValueError()
                        manager.events(run_id)
                        self.stream(run_id, after)
                    else:
                        self.send_json(404, {"error": "Not found"})
                except KeyError:
                    self.send_json(404, {"error": "Unknown run"})
                except ValueError:
                    self.send_json(400, {"error": "Invalid event cursor"})
                return
            self.send_json(404, {"error": "Not found"})

        def stream(self, run_id, after):
            self.send_studio_headers(200, "text/event-stream; charset=utf-8")
            self.close_connection = True
            try:
                while True:
                    events = manager.events(run_id, after)
                    for event in events:
                        self.wfile.write(f"id: {event['seq']}\ndata: {json.dumps(event)}\n\n".encode())
                        self.wfile.flush()
                        after = event["seq"]
                    with manager.condition:
                        # A final event may arrive between the snapshot and this lock.
                        # Deliver it before closing; never strand a client at suite_finished.
                        if after < len(manager.runs[run_id]):
                            continue
                        if manager.runs[run_id][-1]["kind"] == "run_finished":
                            break
                        manager.condition.wait(timeout=0.5)
                    if not events:
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass  # Browser may leave; the run persists and can be reopened.

        def do_POST(self):
            self.close_connection = True
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.send_json(400, {"error": "Invalid content length"})
                return
            # Drain a bounded body before rejecting Origin/Host. Closing with
            # unread request bytes can reset a loopback connection on Windows.
            body = self.rfile.read(length) if 0 < length <= 2048 else b""
            if not self.authorized(mutation=True):
                return
            if self.path != "/api/runs":
                self.send_json(404, {"error": "Not found"})
                return
            try:
                if not 0 < length <= 2048 or self.headers.get_content_type() != "application/json":
                    raise ValueError("Use a small JSON run request")
                data = json.loads(body)
                if not isinstance(data, dict) or set(data) != {"kata_id", "target"}:
                    raise ValueError("Provide only kata_id and target")
                if not all(isinstance(data[key], str) for key in data):
                    raise ValueError("kata_id and target must be strings")
                run_id = manager.start(data["kata_id"], data["target"])
                self.send_json(201, {"run_id": run_id})
            except BusyError as exc:
                self.send_json(409, {"error": str(exc)})
            except (ValueError, TypeError) as exc:
                self.send_json(400, {"error": str(exc)})

    class StudioServer(ThreadingHTTPServer):
        daemon_threads = True

        def server_close(self):
            super().server_close()
            ownership.close()

    server = None
    try:
        server = StudioServer(("127.0.0.1", port), Handler)
        manager = RunManager(root, state_dir, timeout)
        server.manager = manager
        return server
    except Exception:
        if server:
            server.server_close()
        else:
            ownership.close()
        raise
