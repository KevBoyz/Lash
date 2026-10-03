import json
import platform
from pathlib import Path


# ── macro ──────────────────────────────────────────────────


def get_data_dir() -> Path:
    d = Path.home() / ".lash" / "data" / "macro"
    d.mkdir(parents=True, exist_ok=True)
    return d


def macro_path(name: str) -> Path:
    p = (get_data_dir() / f"{name}.json").resolve()
    if p.parent != get_data_dir().resolve():
        raise ValueError(f"Invalid macro name: '{name}'")
    return p


def save_macro(name: str, data: dict) -> None:
    macro_path(name).write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_macro(name: str) -> dict:
    p = macro_path(name)
    if not p.exists():
        raise FileNotFoundError(name)
    return json.loads(p.read_text(encoding="utf-8"))


def list_macro_files() -> list:
    files = get_data_dir().glob("*.json")
    macros = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            _ = data["name"], data["created_at"], data["duration"]
            macros.append(data)
        except (json.JSONDecodeError, KeyError, OSError):
            continue
    return sorted(macros, key=lambda m: m.get("created_at", ""), reverse=True)


def rename_macro_file(old: str, new: str) -> None:
    src = macro_path(old)
    dst = macro_path(new)
    if not src.exists():
        raise FileNotFoundError(old)
    if dst.exists():
        raise FileExistsError(new)
    data = json.loads(src.read_text(encoding="utf-8"))
    data["name"] = new
    tmp = dst.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.rename(dst)
    src.unlink()


def delete_macro_file(name: str) -> None:
    p = macro_path(name)
    if not p.exists():
        raise FileNotFoundError(name)
    p.unlink()


def serialize_key(key) -> str | dict | None:
    import enum

    if isinstance(key, enum.Enum):
        return f"Key.{key.name}"
    # A character depends on the modifiers currently held: Ctrl+V can be
    # '\x16', Shift+V is 'V', and some combinations have no character at all.
    # Replaying that text loses the actual key needed by keyboard shortcuts.
    vk = getattr(key, "vk", None)
    if isinstance(vk, int):
        data = {"vk": vk}
        for name in ("_scan", "_flags"):
            value = getattr(key, name, None)
            if isinstance(value, int):
                data[name] = value
        return data
    if getattr(key, "char", None) is not None:
        return key.char
    return None


def deserialize_key(s: str | dict, *, hotkey: bool = False):
    if isinstance(s, dict):
        import pynput.keyboard as kb

        extensions = {
            name: s[name]
            for name in ("_scan", "_flags")
            if name in s and name in kb.KeyCode._PLATFORM_EXTENSIONS
        }
        # Keep char unset so pynput cannot turn a physical key into Unicode
        # text, or defer a dead key, when resolving Shift/AltGr combinations.
        return kb.KeyCode.from_vk(s["vk"], **extensions)
    if s.startswith("Key."):
        import pynput.keyboard as kb

        return getattr(kb.Key, s[4:])
    # Older recordings stored Ctrl+A..Z as ASCII control characters. Named
    # keys such as Tab and Enter were stored separately as Key.tab/Key.enter.
    if len(s) == 1 and 1 <= ord(s) <= 26:
        s = chr(ord(s) + ord("a") - 1)
    if hotkey and len(s) == 1 and platform.system() == "Windows":
        import ctypes
        import pynput.keyboard as kb

        # Recover legacy shifted letters and punctuation using the active
        # layout. Modifier down/up events are already present in the macro.
        key_scan = ctypes.windll.user32.VkKeyScanW
        key_scan.argtypes = (ctypes.c_wchar,)
        key_scan.restype = ctypes.c_short
        code = key_scan(s)
        if code != -1:
            return kb.KeyCode.from_vk(code & 0xFF)
    return s


def minimize_terminal() -> None:
    if platform.system() == "Windows":
        try:
            import ctypes

            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
        except Exception:
            pass
    else:
        try:
            import sys

            sys.stdout.write("\x1b[2t")  # xterm minimize protocol
            sys.stdout.flush()
        except Exception:
            pass
