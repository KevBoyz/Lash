import click
from os import system
from time import sleep
from datetime import datetime
from lash.plugins.sched.core import reg_crono, time_format


@click.group('sched', help='Schedule tasks at the command line level')
def sched():
    pass


@sched.command()
@click.argument('command', metavar='command', type=click.STRING)
@click.argument('h', metavar='<hours>', type=click.INT, required=False, default=0)
@click.argument('m', metavar='<minutes>', type=click.INT, required=False, default=0)
@click.argument('s', metavar='<seconds>', type=click.INT, required=False, default=0)
def run(command, s, m, h):
    """\b
       Run a command repeatedly at a given interval.

       \b
       Example: sched run "python sync.py" 0 0 30 """
    if h <= 0 and m <= 0 and s <= 0:
        print('Error: Time delay is not defined')
        return
    t = h * 3600 + m * 60 + s
    while True:
        h2, m2, s2 = h, m, s
        for i in range(0, t):
            h2, m2, s2 = reg_crono(h2, m2, s2)
            fh, fm, fs = time_format(h2, m2, s2)
            print(f'Time remaining: {fh}:{fm}:{fs}', end="\r")
            sleep(1)
        print('Time remaining: 00:00:00 ', end="\r")
        system(command=command)
        print()


@sched.command()
@click.argument('command', metavar='command', type=click.STRING)
@click.argument('h', metavar='<hours>', type=click.INT, required=False, default=0)
@click.argument('m', metavar='<minutes>', type=click.INT, required=False, default=0)
@click.argument('s', metavar='<seconds>', type=click.INT, required=False, default=0)
def wait(command, h, m, s):
    """
        Wait a given time, run a command once and exit.

        \b
        Example: sched wait "python backup.py" 0 0 10
    """
    t = h * 3600 + m * 60 + s
    for i in range(0, t):
        h, m, s = reg_crono(h, m, s)
        fh, fm, fs = time_format(h, m, s)
        print(f'Time remaining: {fh}:{fm}:{fs}', end="\r")
        sleep(1)
    print('Time remaining: 00:00:00 ', end="\r")
    system(command=command)


@sched.command()
@click.argument('time', metavar='time', type=click.STRING)
@click.argument('command', metavar='<command>', type=click.STRING)
def exec(time, command):
    """\b
        Execute a command from determined moment of day.

        \b
        The time needs this syntax: HH:MM:SS, e.g. 10:30:0
        Example: exec 15:25:0 "help"
    """
    parts = time.split(':')
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        print('ERROR: syntax incorrect, use HH:MM:SS format, e.g. 10:30:0')
        return
    target_h, target_m, target_s = int(parts[0]), int(parts[1]), int(parts[2])
    while (datetime.now().hour, datetime.now().minute, datetime.now().second) != (target_h, target_m, target_s):
        now = datetime.now()
        print(f' Waiting {now.hour}:{now.minute}:{now.second} -> {time}', end='\r')
    system(command=command)
