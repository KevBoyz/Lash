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
