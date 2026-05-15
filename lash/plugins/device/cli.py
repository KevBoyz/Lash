import click
from keyboard import is_pressed
from lash.plugins.device.core import (
    run_keyhold, run_autoclick_single, run_autoclick_double,
    run_autoclick_hold, run_autoclick_repeat,
    record_macro, play_macro, list_macros, rename_macro, delete_macro,
)
from lash.plugins.device.helpers import minimize_terminal


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


@click.command(help='Record and play keyboard/mouse macros')
@click.option('-r', '--record',  'action', flag_value='record',  help='Record a new macro')
@click.option('-p', '--play',    'action', flag_value='play',    help='Play a macro')
@click.option('-l', '--list',    'action', flag_value='list',    help='List saved macros')
@click.option('-d', '--delete',  'action', flag_value='delete',  help='Delete a macro')
@click.option('--rename',        'action', flag_value='rename',  help='Rename a macro')
@click.argument('name',   required=False)
@click.argument('newname', required=False)
@click.option('-n',           type=int,   default=1,    help='Repeat N times (with -p)')
@click.option('--loop',       is_flag=True,             help='Loop indefinitely (with -p), F3 to stop')
@click.option('--speed',      type=float, default=1.0,  help='Playback speed multiplier (with -p)')
@click.option('--full-speed', is_flag=True,             help='No delays between events (with -p)')
def macro(action, name, newname, n, loop, speed, full_speed):
    if action is None:
        raise click.UsageError("Specify an action: -r, -p, -l, -d, or --rename")

    if action == 'list':
        macros = list_macros()
        if not macros:
            click.echo('No macros saved.')
            return
        click.echo(f"{'NAME':<15} {'CREATED':<20} {'DURATION'}")
        for m in macros:
            created = m['created_at'].replace('T', ' ')[:16]
            click.echo(f"{m['name']:<15} {created:<20} {m['duration']}s")
        return

    if action == 'record':
        if not name:
            raise click.UsageError("-r requires a macro name")
        click.echo(f"Recording '{name}'... press F3 to stop")
        try:
            result = record_macro(name)
        except ValueError as e:
            raise click.ClickException(str(e))
        if result is None:
            click.echo('Nothing recorded.')
        else:
            click.echo(f"Macro '{name}' saved ({result['duration']}s, {len(result['events'])} events)")
        return

    if action == 'play':
        if not name:
            raise click.UsageError("-p requires a macro name")
        if speed != 1.0 and full_speed:
            raise click.UsageError("--speed and --full-speed are mutually exclusive")
        if loop and n != 1:
            raise click.UsageError("--loop and -n are mutually exclusive")
        if loop:
            click.echo(f"Playing '{name}' (loop, F3 to stop)...")
        else:
            label = f"run 1/{n}" if n > 1 else "1x"
            click.echo(f"Playing '{name}' ({label})...")
        minimize_terminal()
        try:
            play_macro(name, speed=speed, full_speed=full_speed, repeat=n, loop=loop)
        except ValueError as e:
            raise click.ClickException(str(e))
        return

    if action == 'rename':
        if not name or not newname:
            raise click.UsageError("--rename requires <old> <new>")
        try:
            rename_macro(name, newname)
        except ValueError as e:
            raise click.ClickException(str(e))
        click.echo(f"Macro '{name}' renamed to '{newname}'")
        return

    if action == 'delete':
        if not name:
            raise click.UsageError("-d requires a macro name")
        try:
            delete_macro(name)
        except ValueError as e:
            raise click.ClickException(str(e))
        click.echo(f"Macro '{name}' deleted")
        return
