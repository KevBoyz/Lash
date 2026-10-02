import json
import shutil
from pathlib import Path
from datetime import datetime
from uuid import uuid4


def _default_data_dir() -> Path:
    return Path.home() / ".lash" / "data" / "todo"


def _config_path() -> Path:
    return _default_data_dir() / "config.json"


def load_config() -> dict:
    path = _config_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_config(cfg: dict) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def resolve_data_dir() -> Path:
    cfg = load_config()
    override = cfg.get("data_dir")
    if override:
        return Path(override).expanduser()
    return _default_data_dir()


def data_dir() -> Path:
    d = resolve_data_dir()
    d.mkdir(parents=True, exist_ok=True)
    legacy = Path.home() / ".lash" / "data" / "work"
    if legacy.exists():
        for name in ("tasks.json", "sessions.json"):
            src = legacy / name
            dst = d / name
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)
    return d


def set_data_dir(new_path: Path) -> Path:
    new_path = Path(new_path).expanduser().resolve()
    new_path.mkdir(parents=True, exist_ok=True)
    cfg = load_config()
    cfg["data_dir"] = str(new_path)
    save_config(cfg)
    return new_path


def clear_records(path: Path) -> None:
    tasks = path / "tasks.json"
    sessions = path / "sessions.json"
    tasks.write_text(json.dumps({"tasks": [], "active": None}, indent=2),
                     encoding="utf-8")
    sessions.write_text("[]", encoding="utf-8")


def format_duration(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def format_minutes_short(minutes: int) -> str:
    if minutes <= 0:
        return "0min"
    h = minutes // 60
    m = minutes % 60
    if h and m:
        return f"{h}h{m:02d}min"
    if h:
        return f"{h}h"
    return f"{m}min"


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
