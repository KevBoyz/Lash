from time import sleep


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
