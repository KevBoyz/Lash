import json
from datetime import datetime, date
from pathlib import Path
from lash.plugins.work.helpers import now_iso, generate_id, find_task


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"tasks": [], "active": None}
    with open(path) as f:
        return json.load(f)


def save_state(path: Path, state: dict) -> None:
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def load_sessions(path: Path) -> list:
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def append_session(path: Path, entry: dict) -> None:
    sessions = load_sessions(path)
    sessions.append(entry)
    with open(path, "w") as f:
        json.dump(sessions, f, indent=2)
