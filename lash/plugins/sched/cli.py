import click
from os import system
from time import sleep
from datetime import datetime
from rich import print
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from lash.plugins.sched.core import reg_crono, time_format

_console = Console()

_progress_columns = [
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TimeElapsedColumn(),
]


@click.group("sched", help="Schedule tasks at the command line level")
def sched():
    pass


@sched.command()
@click.argument("command", metavar="command", type=click.STRING)
@click.argument("h",
                metavar="<hours>",
                type=click.INT,
                required=False,
                default=0)
@click.argument("m",
                metavar="<minutes>",
                type=click.INT,
                required=False,
                default=0)
@click.argument("s",
                metavar="<seconds>",
                type=click.INT,
                required=False,
                default=0)
def run(command, s, m, h):
    """\b
    Run a command repeatedly at a given interval.

    \b
    Example: sched run "python sync.py" 0 0 30"""
    if h <= 0 and m <= 0 and s <= 0:
        print("[red]Error:[/red] Time delay is not defined")
        return
    t = h * 3600 + m * 60 + s
    while True:
        h2, m2, s2 = h, m, s
        with Progress(*_progress_columns, transient=True) as prog:
            task = prog.add_task("Time remaining", total=t)
            for i in range(0, t):
                h2, m2, s2 = reg_crono(h2, m2, s2)
                fh, fm, fs = time_format(h2, m2, s2)
                prog.update(
                    task,
                    advance=1,
                    description=(
                        f"Time remaining: {fh}:{fm}:{fs}"
                    ),
                )
                sleep(1)
        system(command=command)


@sched.command()
@click.argument("command", metavar="command", type=click.STRING)
@click.argument("h",
                metavar="<hours>",
                type=click.INT,
                required=False,
                default=0)
@click.argument("m",
                metavar="<minutes>",
                type=click.INT,
                required=False,
                default=0)
@click.argument("s",
                metavar="<seconds>",
                type=click.INT,
                required=False,
                default=0)
def wait(command, h, m, s):
    """
    Wait a given time, run a command once and exit.

    \b
    Example: sched wait "python backup.py" 0 0 10
    """
    t = h * 3600 + m * 60 + s
    with Progress(*_progress_columns, transient=True) as prog:
        task = prog.add_task("Time remaining", total=t)
        for i in range(0, t):
            h, m, s = reg_crono(h, m, s)
            fh, fm, fs = time_format(h, m, s)
            prog.update(
                task,
                advance=1,
                description=(
                    f"Time remaining: {fh}:{fm}:{fs}"
                ),
            )
            sleep(1)
    system(command=command)


@sched.command()
@click.argument("time", metavar="time", type=click.STRING)
@click.argument("command", metavar="<command>", type=click.STRING)
def exec(time, command):
    """\b
    Execute a command from determined moment of day.

    \b
    The time needs this syntax: HH:MM:SS, e.g. 10:30:0
    Example: exec 15:25:0 "help"
    """
    parts = time.split(":")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        print(
            "[red]ERROR:[/red] syntax incorrect, use HH:MM:SS format, "
            "e.g. 10:30:0"
        )
        return
    target_h, target_m, target_s = int(parts[0]), int(parts[1]), int(parts[2])
    with _console.status(
        f"Waiting {datetime.now().hour}:{datetime.now().minute}:{datetime.now().second} -> {time}"
    ) as status:
        while (
            datetime.now().hour,
            datetime.now().minute,
            datetime.now().second) != (
            target_h,
            target_m,
            target_s,
        ):
            now = datetime.now()
            status.update(
                f"Waiting {
                    now.hour}:{
                    now.minute}:{
                    now.second} -> {time}")
            sleep(1)
    system(command=command)
