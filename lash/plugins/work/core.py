import json
from datetime import datetime, date
from pathlib import Path
from lash.plugins.work.helpers import now_iso, generate_id, find_task


# ── shared ────────────────────────────────────────────────────────────────────


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


# ── rm ────────────────────────────────────────────────────────────────────────


def remove_task(state: dict, query: str) -> dict:
    pending = [t for t in state["tasks"] if not t["done"]]
    task = find_task(pending, query)
    if not task:
        raise ValueError(f"Task '{query}' not found")
    if state["active"] and state["active"]["task_id"] == task["id"]:
        raise ValueError("Cannot remove active task. Stop it first.")
    state["tasks"] = [t for t in state["tasks"] if t["id"] != task["id"]]
    return task


# ── start ─────────────────────────────────────────────────────────────────────


def start_task(state: dict, task_id: str, pomo: bool = False,
               pomo_work_mins: int = 25, pomo_break_mins: int = 5) -> None:
    if state["active"]:
        raise ValueError("Another task is already active")
    task = next(t for t in state["tasks"] if t["id"] == task_id)
    state["active"] = {
        "task_id": task_id,
        "segments": list(task.get("accumulated_segments", [])),
        "current_start": now_iso(),
        "is_paused": False,
        "pomo": pomo,
        "pomo_work_mins": pomo_work_mins,
        "pomo_break_mins": pomo_break_mins,
        "pomo_sessions": 0,
    }


# ── pause ─────────────────────────────────────────────────────────────────────


def pause_task(state: dict) -> str:
    active = state["active"]
    if not active:
        raise ValueError("No active task")
    if active["is_paused"]:
        active["current_start"] = now_iso()
        active["is_paused"] = False
        return "resumed"
    active["segments"].append({"start": active["current_start"], "end": now_iso()})
    active["current_start"] = None
    active["is_paused"] = True
    return "paused"


# ── status ────────────────────────────────────────────────────────────────────


def calc_elapsed(active: dict) -> int:
    total = 0
    for seg in active["segments"]:
        start = datetime.fromisoformat(seg["start"])
        end = datetime.fromisoformat(seg["end"])
        total += int((end - start).total_seconds())
    if not active["is_paused"] and active.get("current_start"):
        start = datetime.fromisoformat(active["current_start"])
        total += int((datetime.now() - start).total_seconds())
    return total


# ── stop ──────────────────────────────────────────────────────────────────────


def stop_task(state: dict, done: bool) -> dict | None:
    active = state["active"]
    if not active:
        raise ValueError("No active task")
    if not active["is_paused"] and active.get("current_start"):
        active["segments"].append({"start": active["current_start"], "end": now_iso()})
    task = next(t for t in state["tasks"] if t["id"] == active["task_id"])
    total_seconds = sum(
        int((datetime.fromisoformat(s["end"]) - datetime.fromisoformat(s["start"])).total_seconds())
        for s in active["segments"]
    )
    session_entry = None
    if done:
        task["done"] = True
        task["done_at"] = now_iso()
        task["accumulated_segments"] = []
        session_entry = {
            "task_id": active["task_id"],
            "task_name": task["name"],
            "date": date.today().isoformat(),
            "total_minutes": total_seconds // 60,
            "pomo_sessions": active["pomo_sessions"],
            "done": True,
        }
    else:
        task["accumulated_segments"] = active["segments"]
    state["active"] = None
    return session_entry


# ── log ───────────────────────────────────────────────────────────────────────


def format_log(sessions: list) -> list:
    from collections import defaultdict
    grouped = defaultdict(lambda: {"total_minutes": 0, "tasks": []})
    for s in sessions:
        grouped[s["date"]]["total_minutes"] += s["total_minutes"]
        grouped[s["date"]]["tasks"].append({
            "name": s["task_name"],
            "minutes": s["total_minutes"],
            "pomo_sessions": s["pomo_sessions"],
        })
    return [{"date": d, **v} for d, v in sorted(grouped.items(), reverse=True)]
