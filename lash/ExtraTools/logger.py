import os, click
from pynput.keyboard import Listener
from ..Exportables.ikeyboard import *
from ..executor import playbp


@click.group('spy', help='Spy tools')
def spy():
    ...


@spy.command(help='Keylogger')
@click.option('-p', type=click.Path(exists=True), default='.', help='Path to send output file with info')
def keyboard(p):
    print('<key logger on> f3 to stop record')
    os.chdir(p)
    listener = Listener(on_press=key_down, on_release=key_up)
    listener.start()
    listener.join()
    playbp()
    print(f'> Process Finished <')