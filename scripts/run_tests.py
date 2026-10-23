"""Run offline suites in separate interpreters to avoid kata module collisions."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from studio.registry import load_katas


def main():
    environment = dict(os.environ)
    environment.pop("KATA_MODULE", None)
    suites = ["tests/unit", "tests/studio"] + [f"katas/{k['id']}" for k in load_katas() if k["available"]]
    for folder in suites:
        print(f"\n--- {folder} ---", flush=True)
        result = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", folder,
                                 "-p", "test_*.py", "-v"], cwd=ROOT, env=environment)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
