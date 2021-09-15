import click
from pynput.mouse import Controller, Button
from keyboard import is_pressed
from time import sleep


@click.command(help='Auto clicker')
@click.option('-cd', type=click.FLOAT, default=0.0, help='Click delay (seconds)')
@click.option('-ch', is_flag=True, default=False, show_default=True, help='Enable click and hold')
def autoclick(cd, ch):
    mouse = Controller()
    if not ch:
        print('Auto Clicker initialized, f4 to start f3 to stop')
    else:
        print('Auto Clicker initialized, f4 to start, *click* to stop')
    if ch:
        while True:
            if is_pressed('f4'):
                break
        try:
            with mouse.press(Button.left):
                pass
        except:
            pass
    else:
        while True:
            if is_pressed('f4'):
                while True:
                    if is_pressed('f3'):
                        break
                    else:
                        sleep(cd)
                        mouse.press(Button.left)
                        mouse.release(Button.left)
            else:
                continue
