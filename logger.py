import os, click
from pynput.keyboard import Listener
from Exportables.ikeyboard import *


@click.group('log', help='Simple loggers to rec events')
def log():
    ...


@log.command(help='Keyboard listener')
@click.option('-p', type=click.Path(exists=True), default='.', help='Path to send output file with info')
def keyboard(p):
    os.chdir(p)
    listener = Listener(on_press=key_down, on_release=key_up)
    listener.start()
    listener.join()
    print(f'> Process Finished <')


