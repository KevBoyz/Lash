from time import sleep, time
import threading
from lash.plugins.macro.helpers import (
    list_macro_files,
    rename_macro_file,
    delete_macro_file,
    load_macro,
    deserialize_key,
    macro_path,
    save_macro,
    serialize_key,
    minimize_terminal,
)


def list_macros() -> list:
    return list_macro_files()


def rename_macro(old: str, new: str) -> None:
    try:
        rename_macro_file(old, new)
    except FileNotFoundError:
        raise ValueError(f"macro '{old}' not found")
    except FileExistsError:
        raise ValueError(f"macro '{new}' already exists")


def delete_macro(name: str) -> None:
    try:
        delete_macro_file(name)
    except FileNotFoundError:
        raise ValueError(f"macro '{name}' not found")


def _kb_controller():
    import pynput.keyboard as kb

    return kb.Controller()


def _mouse_controller():
    from pynput.mouse import Controller

    return Controller()


def _dispatch_key_event(event, kb_ctrl, held):
    hotkey = any(
        getattr(key, "name", "").split("_")[0]
        in ("ctrl", "alt", "shift", "cmd")
        for key in held
    )
    key = deserialize_key(event["key"], hotkey=hotkey)
    if event["type"] == "key_down":
        if key not in held:
            held.append(key)
        kb_ctrl.press(key)
    else:
        # A legacy character may change when its modifier is released
        # first (e.g. Ctrl+V down='\x16', up='v'). Release the held key.
        if key not in held and isinstance(event["key"], str):
            physical_key = deserialize_key(event["key"], hotkey=True)
            if physical_key in held:
                key = physical_key
        kb_ctrl.release(key)
        if key in held:
            held.remove(key)


def _dispatch_event(event, kb_ctrl, mouse_ctrl, pressed_keys=None):
    t = event["type"]
    if t in ("key_down", "key_up"):
        held = pressed_keys if pressed_keys is not None else []
        _dispatch_key_event(event, kb_ctrl, held)
    elif t == "mouse_move":
        mouse_ctrl.position = (event["x"], event["y"])
    elif t in ("mouse_down", "mouse_up"):
        from pynput.mouse import Button

        btn = getattr(Button, event["button"])
        if "x" in event:
            mouse_ctrl.position = (event["x"], event["y"])
        if t == "mouse_down":
            mouse_ctrl.press(btn)
        else:
            mouse_ctrl.release(btn)
    elif t == "mouse_scroll":
        mouse_ctrl.scroll(event["dx"], event["dy"])


def record_macro(name: str) -> dict | None:  # noqa: C901
    if macro_path(name).exists():
        raise ValueError(f"macro '{name}' already exists. Delete it first.")

    import importlib

    kb = importlib.import_module("pynput.keyboard")
    mouse_mod = importlib.import_module("pynput.mouse")
    MouseListener = mouse_mod.Listener

    events = []
    start_time = [None]
    last_move_time = [0.0]
    stop_event = threading.Event()
    # Controller.position getter uses GetCursorPos (logical/DPI-scaled coords).
    # WH_MOUSE_LL callbacks give physical coords — mismatches SetCursorPos on scaled displays.
    # Reading via controller ensures record and playback share the same
    # coordinate space.
    _read_ctrl = _mouse_controller()

    def elapsed():
        return time() - start_time[0] if start_time[0] is not None else 0.0

    def on_press(key):
        if stop_event.is_set():
            return
        if start_time[0] is None:
            start_time[0] = time()
        if hasattr(key, "_value_") and key == kb.Key.f3:
            stop_event.set()
            return
        serialized = serialize_key(key)
        if serialized is None:
            return
        events.append({"t": elapsed(), "type": "key_down", "key": serialized})

    def on_release(key):
        if start_time[0] is None or stop_event.is_set():
            return
        if hasattr(key, "_value_") and key == kb.Key.f3:
            return
        serialized = serialize_key(key)
        if serialized is None:
            return
        events.append({"t": elapsed(), "type": "key_up", "key": serialized})

    def on_move(x, y):
        if start_time[0] is None:
            start_time[0] = time()
        t = elapsed()
        if last_move_time[0] > 0 and t - last_move_time[0] < 0.016:
            return
        last_move_time[0] = t
        lx, ly = _read_ctrl.position
        events.append({"t": t, "type": "mouse_move", "x": lx, "y": ly})

    def on_click(x, y, button, pressed):
        if start_time[0] is None:
            start_time[0] = time()
        btn_name = button.name
        etype = "mouse_down" if pressed else "mouse_up"
        lx, ly = _read_ctrl.position
        events.append(
            {
                "t": elapsed(),
                "type": etype,
                "button": btn_name,
                "x": lx,
                "y": ly,
            }
        )

    def on_scroll(x, y, dx, dy):
        if start_time[0] is None:
            start_time[0] = time()
        events.append(
            {
                "t": elapsed(),
                "type": "mouse_scroll",
                "dx": dx,
                "dy": dy,
            }
        )

    minimize_terminal()

    with kb.Listener(on_press=on_press, on_release=on_release):
        with MouseListener(on_move=on_move, on_click=on_click, on_scroll=on_scroll):
            stop_event.wait()

    if not events:
        return None

    from datetime import datetime

    duration = events[-1]["t"]
    data = {
        "name": name,
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "duration": round(duration, 3),
        "events": events,
    }
    save_macro(name, data)
    return data


_MIN_EVENT_DELAY = (
    0.001  # 1ms floor — prevents event loss when OS/app can't drain queue fast enough
)


def _interruptible_sleep(seconds: float, stop: threading.Event) -> None:
    end = time() + seconds
    while True:
        remaining = end - time()
        if remaining <= 0:
            break
        if stop.is_set():
            return
        sleep(min(0.01, remaining))


def _load_macro_data(name: str) -> dict:
    try:
        return load_macro(name)
    except FileNotFoundError:
        raise ValueError(f"macro '{name}' not found")


def _calculate_delay_factor(speed: float, full_speed: bool) -> float:
    return 0 if full_speed else (1 / speed if speed else 1.0)


def _setup_f3_watcher() -> tuple[
    threading.Event,
    threading.Event,
    threading.Thread,
]:
    force_stopped = threading.Event()
    done = threading.Event()

    def _watch_f3():
        from keyboard import is_pressed

        while not done.is_set():
            if is_pressed("f3"):
                force_stopped.set()
                break
            sleep(0.05)

    watcher = threading.Thread(target=_watch_f3, daemon=True)
    watcher.start()
    return force_stopped, done, watcher


def _run_macro_once(
    events: list,
    delay_factor: float,
    force_stopped: threading.Event,
    kb_ctrl,
    mouse_ctrl,
) -> None:
    run_start = time()
    last_dispatch = time()
    pressed_keys = []
    try:
        for event in events:
            if force_stopped.is_set():
                return
            remaining = run_start + event["t"] * delay_factor - time()
            if remaining > _MIN_EVENT_DELAY:
                _interruptible_sleep(remaining, force_stopped)
            else:
                gap = _MIN_EVENT_DELAY - (time() - last_dispatch)
                if gap > 0:
                    sleep(gap)
            if force_stopped.is_set():
                return
            _dispatch_event(event, kb_ctrl, mouse_ctrl, pressed_keys)
            last_dispatch = time()
    finally:
        _release_pressed_keys(pressed_keys, kb_ctrl)


def _release_pressed_keys(pressed_keys, kb_ctrl):
    error = None
    for key in reversed(pressed_keys):
        try:
            kb_ctrl.release(key)
        except Exception as exc:
            # Still release the remaining modifiers if one release fails.
            if error is None:
                error = exc
    if error is not None:
        raise error


def _run_macro_loop(
    events: list,
    delay_factor: float,
    force_stopped: threading.Event,
    kb_ctrl,
    mouse_ctrl,
    repeat: int,
    loop: bool,
) -> None:
    if loop:
        while not force_stopped.is_set():
            _run_macro_once(events, delay_factor, force_stopped, kb_ctrl, mouse_ctrl)
    else:
        for _ in range(repeat):
            if force_stopped.is_set():
                break
            _run_macro_once(events, delay_factor, force_stopped, kb_ctrl, mouse_ctrl)


def play_macro(name: str, speed: float, full_speed: bool, repeat: int, loop: bool) -> bool:
    data = _load_macro_data(name)
    events = data["events"]
    delay_factor = _calculate_delay_factor(speed, full_speed)

    kb_ctrl = _kb_controller()
    mouse_ctrl = _mouse_controller()

    force_stopped, done, watcher = _setup_f3_watcher()

    try:
        _run_macro_loop(
            events, delay_factor, force_stopped, kb_ctrl, mouse_ctrl, repeat, loop
        )
    finally:
        done.set()
        watcher.join(timeout=0.2)
    return force_stopped.is_set()
