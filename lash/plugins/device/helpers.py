import json
import platform
from pathlib import Path


def get_data_dir() -> Path:
    d = Path.home() / '.lash' / 'data' / 'device'
    d.mkdir(parents=True, exist_ok=True)
    return d


def macro_path(name: str) -> Path:
    p = (get_data_dir() / f'{name}.json').resolve()
    if p.parent != get_data_dir().resolve():
        raise ValueError(f"Invalid macro name: '{name}'")
    return p


def save_macro(name: str, data: dict) -> None:
    macro_path(name).write_text(json.dumps(data, indent=2), encoding='utf-8')


def load_macro(name: str) -> dict:
    p = macro_path(name)
    if not p.exists():
        raise FileNotFoundError(name)
    return json.loads(p.read_text(encoding='utf-8'))


def list_macro_files() -> list:
    files = get_data_dir().glob('*.json')
    macros = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            _ = data['name'], data['created_at'], data['duration']
            macros.append(data)
        except (json.JSONDecodeError, KeyError, OSError):
            continue
    return sorted(macros, key=lambda m: m.get('created_at', ''), reverse=True)


def rename_macro_file(old: str, new: str) -> None:
    src = macro_path(old)
    dst = macro_path(new)
    if not src.exists():
        raise FileNotFoundError(old)
    if dst.exists():
        raise FileExistsError(new)
    data = json.loads(src.read_text(encoding='utf-8'))
    data['name'] = new
    tmp = dst.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2), encoding='utf-8')
    tmp.rename(dst)
    src.unlink()


def delete_macro_file(name: str) -> None:
    p = macro_path(name)
    if not p.exists():
        raise FileNotFoundError(name)
    p.unlink()


def serialize_key(key) -> str | None:
    if hasattr(key, 'char') and key.char is not None:
        return key.char
    try:
        s = str(key).replace('pynput.keyboard.Key.', 'Key.')
        if s.startswith('Key.'):
            return s
        return None
    except Exception:
        return None


def deserialize_key(s: str):
    import pynput.keyboard as kb
    if s.startswith('Key.'):
        attr = s[4:]
        return getattr(kb.Key, attr)
    return s


def minimize_terminal() -> None:
    if platform.system() != 'Windows':
        return
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
    except Exception:
        pass
