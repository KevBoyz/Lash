from time import sleep, time
import threading
from lash.plugins.device.helpers import (
    list_macro_files, rename_macro_file, delete_macro_file,
    load_macro, deserialize_key, macro_path, save_macro, serialize_key, minimize_terminal,
)


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
    import pynput.keyboard as kb
    from pynput.mouse import Button

    t = event['type']
    if t == 'key_down':
        kb_ctrl.press(deserialize_key(event['key']))
    elif t == 'key_up':
        kb_ctrl.release(deserialize_key(event['key']))
    elif t == 'mouse_move':
        mouse_ctrl.position = (event['x'], event['y'])
    elif t in ('mouse_down', 'mouse_up'):
        btn = getattr(Button, event['button'])
        if t == 'mouse_down':
            mouse_ctrl.press(btn)
        else:
            mouse_ctrl.release(btn)
    elif t == 'mouse_scroll':
        mouse_ctrl.scroll(event['dx'], event['dy'])


def play_macro(name: str, speed: float, full_speed: bool, repeat: int, loop: bool) -> None:
    try:
        data = load_macro(name)
    except FileNotFoundError:
        raise ValueError(f"macro '{name}' not found")

    events = data['events']
    delay_factor = 0 if full_speed else (1 / speed if speed else 1.0)

    kb_ctrl = _kb_controller()
    mouse_ctrl = _mouse_controller()

    def run_once():
        for i, event in enumerate(events):
            wait = (event['t'] - events[i - 1]['t']) * delay_factor if i > 0 else 0
            sleep(wait)
            _dispatch_event(event, kb_ctrl, mouse_ctrl)

    if loop:
        from keyboard import is_pressed
        while not is_pressed('f3'):
            run_once()
    else:
        for _ in range(repeat):
            run_once()
