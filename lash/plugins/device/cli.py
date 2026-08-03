import click
from keyboard import is_pressed
from rich import print
from lash.plugins.device.core import (
    run_keyhold,
    run_autoclick_single,
    run_autoclick_double,
    run_autoclick_hold,
    run_autoclick_repeat,
)


@click.group()
def device():
    """Keyboard hold and mouse auto-click automation."""


@click.command(
    short_help="Hold a keyboard key", help="Hold a keyboard key until F3 is pressed"
)
@click.argument("key", metavar="<key>", type=click.STRING)
def keyhold(key):
    click.echo("initialized, f4 to start, f3 to stop")
    while True:
        if is_pressed("f4"):
            click.echo("[== -- *typing* -- ==]")
            break
    try:
        run_keyhold(key)
    except Exception as e:
        print(f"[red]Error:[/red] {e}")


@click.command()
@click.option(
    "-cd", type=click.FLOAT, default=0.0, help="Interval between clicks in seconds"
)
@click.option(
    "-ch",
    is_flag=True,
    default=False,
    show_default=True,
    help="Click and hold mode (click to release)",
)
@click.option(
    "-sg", is_flag=True, default=False, show_default=True, help="Single click and exit"
)
@click.option(
    "-db", is_flag=True, default=False, show_default=True, help="Double click and exit"
)
def autoclick(cd, ch, sg, db):
    """Auto clicker — simulates mouse clicks repeatedly.

    \b
    Default mode: repeats clicks at the given interval.
      F4 to start, F3 to stop.

    \b
    Modes:
      -ch   Click and hold. F4 to start, click to release.
      -sg   Single click immediately and exit.
      -db   Double click immediately and exit.

    \b
    Example:
      lash autoclick -cd 0.5     # click every 0.5 seconds
      lash autoclick -ch         # hold left mouse button
      lash autoclick -sg         # one click and done
    """
    if sg:
        run_autoclick_single()
    elif db:
        run_autoclick_double()
    else:
        if not ch:
            click.echo("Auto Clicker initialized, f4 to start f3 to stop")
        else:
            click.echo("Auto Clicker initialized, f4 to start, *click* to stop")
        if ch:
            run_autoclick_hold()
        else:
            run_autoclick_repeat(cd)


device.add_command(keyhold)
device.add_command(autoclick)
