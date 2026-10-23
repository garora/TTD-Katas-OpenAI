"""Start the loopback-only Studio; no build step or third-party dependencies."""
import argparse
from .server import create_server


def main():
    parser = argparse.ArgumentParser(description="Local, offline TDD Kata Studio")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("port must be between 0 and 65535")
    try:
        server = create_server(args.port)
    except (OSError, RuntimeError) as exc:
        parser.exit(1, f"Cannot start Studio: {exc}\n")
    print(f"TDD Kata Studio: http://127.0.0.1:{server.server_port}", flush=True)
    print("Offline tests only. Ctrl+C stops Studio. Run history: .studio-state/runs/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.manager.close()
        server.server_close()


if __name__ == "__main__":
    main()
