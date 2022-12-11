import click
import pynput.keyboard as kb
from keyboard import is_pressed


@click.command(short_help='Hold a keyboard key')
@click.argument('key', metavar='<key>', type=click.STRING)
def keyhold(key):
    k = kb.Controller()
    print('initialized, f4 to start, f3 to stop')
    while True:
        if is_pressed('f4'):
            print('[== -- *typing* -- ==]')
            break
    try:
        while not is_pressed('f3'):
            k.press(key)
    except:
        pass
    pass
