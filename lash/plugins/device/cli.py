import click
from keyboard import is_pressed
from lash.plugins.device.core import (
    run_keyhold, run_autoclick_single, run_autoclick_double,
    run_autoclick_hold, run_autoclick_repeat,
)


@click.command(short_help='Hold a keyboard key', help='Hold a keyboard key until F3 is pressed')
@click.argument('key', metavar='<key>', type=click.STRING)
def keyhold(key):
    click.echo('initialized, f4 to start, f3 to stop')
    while True:
        if is_pressed('f4'):
            click.echo('[== -- *typing* -- ==]')
            break
    try:
        run_keyhold(key)
    except Exception as e:
        click.echo(f'Error: {e}', err=True)


@click.command(help='Auto clicker')
@click.option('-cd', type=click.FLOAT, default=0.0, help='Click delay (seconds)')
@click.option('-ch', is_flag=True, default=False, show_default=True, help='Enable click and hold')
@click.option('-sg', is_flag=True, default=False, show_default=True, help='Do a single click')
@click.option('-db', is_flag=True, default=False, show_default=True, help='Do a double click')
def autoclick(cd, ch, sg, db):
    if sg:
        run_autoclick_single()
    elif db:
        run_autoclick_double()
    else:
        if not ch:
            click.echo('Auto Clicker initialized, f4 to start f3 to stop')
        else:
            click.echo('Auto Clicker initialized, f4 to start, *click* to stop')
        if ch:
            run_autoclick_hold()
        else:
            run_autoclick_repeat(cd)
