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


def add_task(state: dict, name: str) -> dict:
    for t in state["tasks"]:
        if t["name"].lower() == name.lower() and not t["done"]:
            raise ValueError(f"Task '{name}' already exists")
    task = {
        "id": generate_id(),
        "name": name,
        "created_at": now_iso(),
        "done": False,
        "done_at": None,
        "accumulated_segments": [],
    }
    state["tasks"].append(task)
    return task


def remove_task(state: dict, query: str) -> dict:
    pending = [t for t in state["tasks"] if not t["done"]]
    task = find_task(pending, query)
    if not task:
        raise ValueError(f"Task '{query}' not found")
    if state["active"] and state["active"]["task_id"] == task["id"]:
        raise ValueError("Cannot remove active task. Stop it first.")
    state["tasks"] = [t for t in state["tasks"] if t["id"] != task["id"]]
    return task
