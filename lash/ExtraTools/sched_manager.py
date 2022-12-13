import click
from os import system
from time import sleep
from datetime import datetime
from re import search
from typing import List, Tuple


def reg_crono(h:int, m:int, s:int) -> Tuple[int, int, int]:
    """
    Regressive clocker.

    Takes hrs,mts,scs and regress then. (-1sec)
    Return the values regressed.
    """
    if s > 0:
        s -= 1
    else:
        if m > 0:
            m -= 1
            s = 60
        else:
            if h > 0:
                h -= 1
                m = 60
    return h, m, s


def time_format(*args: int) -> List:
    """
    Take an int and format it to time display:
    1 -> 01, 7 -> 07, 12 -> 12
    """
    fmt = list(map(lambda x:
                         '0' + str(x) if len(str(x)) == 1
                         else str(x), args))
    return fmt


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
       Run the command repetitively at a given interval.

       \b
       Example: run "help" 0 0 5 """
    try:
        if h <= 0 and m <= 0 and s <= 0:
            raise Exception('Error: Time delay is not defined')
    except Exception as e:
        print(e)
    t = h * 3600 + m * 60 + s  # Converting to seconds
    while True:
        h2, m2, s2 = h, m, s
        for i in range(0, t):
            h2, m2, s2 = reg_crono(h2, m2, s2)
            fh, fm, fs = time_format(h2, m2, s2)
            print(f'Time remaining: {fh}:{fm}:{fs}', end="\r")
            sleep(1)
        print(f'Time remaining: 00:00:00 ', end="\r")
        system(command=command)
        print()


@sched.command()
@click.argument('command', metavar='command', type=click.STRING)
@click.argument('h', metavar='<hours>', type=click.INT, required=False, default=0)
@click.argument('m', metavar='<minutes>', type=click.INT, required=False, default=0)
@click.argument('s', metavar='<seconds>', type=click.INT, required=False, default=0)
def wait(command, h, m, s):
    """
        Wait x time, run a command once and exit.

        \b
        Example: wait "help" 0 0 10
    """
    # assert h <= 0 and m <= 0 and s <= 0, 'Error: Time delay is not defined'
    t = h * 3600 + m * 60 + s  # Converting to seconds
    for i in range(0, t):
        h, m, s = reg_crono(h, m, s)
        fh, fm, fs = time_format(h, m, s)
        print(f'Time remaining: {fh}:{fm}:{fs}', end="\r")
        sleep(1)
    print(f'Time remaining: 00:00:00 ', end="\r")
    system(command=command)


@sched.command()
@click.argument('time', metavar='time', type=click.STRING)
@click.argument('command', metavar='<command>', type=click.STRING)
def exec(time, command):
    """\b
        Execute a command from determined moment of day.

        \b
        The time need to have this syntax: 10:30:0
        Example: exec 15:25:0 "help"
    """
    if not search('\d:\d:\d', time):
        return print('ERROR sytax incorrect, try use 10:30:0, 1:4:5 with time')
    if time[-1] and time[-2] == '0':
        time = time[:-1]
        print(time)
    while f'{datetime.now().hour}:{datetime.now().minute}:{datetime.now().second}' != time:
        print(f' Waiting {datetime.now().hour}:{datetime.now().minute}:{datetime.now().second} -> {time}', end='\r')
    system(command=command)
