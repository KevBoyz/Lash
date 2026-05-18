from time import sleep, time
import threading
from lash.plugins.device.helpers import (
    list_macro_files, rename_macro_file, delete_macro_file,
    load_macro, deserialize_key, macro_path, save_macro, serialize_key, minimize_terminal,
)


def key_down(key):
    from pynput.keyboard import Key
    log = open('Keylogger.txt', mode='a')
    try:
        log.write(key.char)
    except AttributeError:
        if key == Key.space:
            log.write(' ')
        elif key == Key.backspace:
            log.write(' <bkp> ')
        elif key == Key.shift:
            log.write(' <shift> ')
        elif key == Key.ctrl_l:
            log.write(' <ctrl_l> ')
        elif key == Key.enter:
            log.write(' <enter> \n')
        else:
            log.write(f' <{key}> ')


def key_up(key):
    from pynput.keyboard import Key
    if key == Key.f3:
        return False


def run_keyhold(key):
    import pynput.keyboard as kb
    from keyboard import is_pressed
    k = kb.Controller()
    while not is_pressed('f3'):
        k.press(key)


def run_autoclick_single():
    from pynput.mouse import Controller, Button
    mouse = Controller()
    mouse.press(Button.left)
    mouse.release(Button.left)


def run_autoclick_double():
    from pynput.mouse import Controller, Button
    mouse = Controller()
    for _ in range(2):
        mouse.press(Button.left)
        mouse.release(Button.left)


def run_autoclick_hold():
    from pynput.mouse import Controller, Button
    from keyboard import is_pressed
    mouse = Controller()
    while True:
        if is_pressed('f4'):
            break
    mouse.press(Button.left)
    while not is_pressed('f3'):
        pass
    mouse.release(Button.left)


def run_autoclick_repeat(cd):
    from pynput.mouse import Controller, Button
    from keyboard import is_pressed
    mouse = Controller()
    while True:
        if is_pressed('f4'):
            while True:
                if is_pressed('f3'):
                    break
                sleep(cd)
                mouse.press(Button.left)
                mouse.release(Button.left)
        else:
            continue


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


def _dispatch_event(event, kb_ctrl, mouse_ctrl):
    t = event['type']
    if t == 'key_down':
        kb_ctrl.press(deserialize_key(event['key']))
    elif t == 'key_up':
        kb_ctrl.release(deserialize_key(event['key']))
    elif t == 'mouse_move':
        mouse_ctrl.position = (event['x'], event['y'])
    elif t in ('mouse_down', 'mouse_up'):
        from pynput.mouse import Button
        btn = getattr(Button, event['button'])
        if t == 'mouse_down':
            mouse_ctrl.press(btn)
        else:
            mouse_ctrl.release(btn)
    elif t == 'mouse_scroll':
        mouse_ctrl.scroll(event['dx'], event['dy'])


def record_macro(name: str) -> dict | None:
    if macro_path(name).exists():
        raise ValueError(f"macro '{name}' already exists. Delete it first.")

    import importlib
    kb = importlib.import_module('pynput.keyboard')
    mouse_mod = importlib.import_module('pynput.mouse')
    MouseListener = mouse_mod.Listener

    events = []
    start_time = [None]
    last_move_time = [0.0]
    stop_event = threading.Event()

    def elapsed():
        return time() - start_time[0] if start_time[0] is not None else 0.0

    def on_press(key):
        if start_time[0] is None:
            start_time[0] = time()
        if hasattr(key, '_value_') and key == kb.Key.f3:
            stop_event.set()
            return
        serialized = serialize_key(key)
        if serialized is None:
            return
        events.append({'t': elapsed(), 'type': 'key_down', 'key': serialized})

    def on_release(key):
        if start_time[0] is None:
            return
        if hasattr(key, '_value_') and key == kb.Key.f3:
            return
        serialized = serialize_key(key)
        if serialized is None:
            return
        events.append({'t': elapsed(), 'type': 'key_up', 'key': serialized})

    def on_move(x, y):
        if start_time[0] is None:
            start_time[0] = time()
        t = elapsed()
        if t - last_move_time[0] < 0.05:
            return
        last_move_time[0] = t
        events.append({'t': t, 'type': 'mouse_move', 'x': x, 'y': y})

    def on_click(x, y, button, pressed):
        if start_time[0] is None:
            start_time[0] = time()
        btn_name = button.name
        etype = 'mouse_down' if pressed else 'mouse_up'
        events.append({'t': elapsed(), 'type': etype, 'button': btn_name})

    def on_scroll(x, y, dx, dy):
        if start_time[0] is None:
            start_time[0] = time()
        events.append({'t': elapsed(), 'type': 'mouse_scroll', 'dx': dx, 'dy': dy})

    minimize_terminal()

    with kb.Listener(on_press=on_press, on_release=on_release):
        with MouseListener(on_move=on_move, on_click=on_click, on_scroll=on_scroll):
            stop_event.wait()

    if not events:
        return None

    from datetime import datetime
    duration = events[-1]['t']
    data = {
        'name': name,
        'created_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'duration': round(duration, 3),
        'events': events,
    }
    save_macro(name, data)
    return data


def play_macro(name: str, speed: float, full_speed: bool, repeat: int, loop: bool) -> bool:
    try:
        data = load_macro(name)
    except FileNotFoundError:
        raise ValueError(f"macro '{name}' not found")

    events = data['events']
    delay_factor = 0 if full_speed else (1 / speed if speed else 1.0)

    kb_ctrl = _kb_controller()
    mouse_ctrl = _mouse_controller()

    force_stopped = threading.Event()
    done = threading.Event()

    def _watch_f3():
        from keyboard import is_pressed
        while not done.is_set():
            if is_pressed('f3'):
                force_stopped.set()
                break
            sleep(0.05)

    watcher = threading.Thread(target=_watch_f3, daemon=True)
    watcher.start()

    def interruptible_sleep(seconds):
        end = time() + seconds
        while time() < end:
            if force_stopped.is_set():
                return
            sleep(min(0.05, end - time()))

    def run_once():
        for i, event in enumerate(events):
            if force_stopped.is_set():
                return
            wait = (event['t'] - events[i - 1]['t']) * delay_factor if i > 0 else 0
            if wait > 0:
                interruptible_sleep(wait)
            if force_stopped.is_set():
                return
            _dispatch_event(event, kb_ctrl, mouse_ctrl)

    if loop:
        while not force_stopped.is_set():
            run_once()
    else:
        for _ in range(repeat):
            if force_stopped.is_set():
                break
            run_once()

    done.set()
    watcher.join(timeout=0.2)
    return force_stopped.is_set()
