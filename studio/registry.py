"""Declarative curriculum discovery; availability is never a test verdict."""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {"starter", "solution", "working"}


def load_katas(root: Path = ROOT) -> list[dict]:
    records = json.loads((root / "studio" / "katas.json").read_text(encoding="utf-8"))
    result = []
    seen = set()
    for item in records:
        kata_id = item["id"]
        if not re.fullmatch(r"[0-9]{2}-[a-z0-9-]+", kata_id) or kata_id in seen:
            raise ValueError("Invalid or duplicate kata ID in registry")
        seen.add(kata_id)
        folder = (root / "katas" / kata_id).resolve()
        if folder.parent != (root / "katas").resolve():
            raise ValueError("Kata path escapes the curriculum")
        available = all((folder / name).is_file() for name in
                        ("README.md", "test_kata.py", "solution.py", "starter.py"))
        result.append({**item, "available": available,
                       "targets": [name for name in ("solution", "starter", "working")
                                   if available and (folder / f"{name}.py").is_file()]})
    return result


def get_kata(kata_id: str, root: Path = ROOT) -> dict:
    for item in load_katas(root):
        if item["id"] == kata_id:
            return item
    raise ValueError("Unknown kata ID")


def validate_target(kata_id: str, target: str, root: Path = ROOT) -> dict:
    kata = get_kata(kata_id, root)
    if not kata["available"]:
        raise ValueError("This kata is planned, not runnable yet")
    if target not in TARGETS or target not in kata["targets"]:
        raise ValueError("Target must be an existing starter, solution, or working module")
    folder = (root / "katas" / kata_id).resolve()
    for name in (f"{target}.py", "test_kata.py", "README.md"):
        if (folder / name).resolve().parent != folder:
            raise ValueError("Kata files must remain inside their registered folder")
    return kata
