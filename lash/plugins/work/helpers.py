from pathlib import Path
from datetime import datetime
from uuid import uuid4


def data_dir() -> Path:
    d = Path.home() / ".lash" / "data" / "work"
    d.mkdir(parents=True, exist_ok=True)
    return d


def format_duration(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def now_iso() -> str:
    return datetime.now().isoformat()


def generate_id() -> str:
    return str(uuid4())


def find_task(tasks: list, query: str) -> dict | None:
    if query.isdigit():
        idx = int(query) - 1
        if 0 <= idx < len(tasks):
            return tasks[idx]
        return None
    for t in tasks:
        if t["name"].lower() == query.lower():
            return t
    return None
