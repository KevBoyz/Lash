import click, schedule as sc
from os import system
from time import sleep
from lash.executor import playbp
from datetime import datetime
from re import search


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
       Run commands repetitively at a given interval starting from
       current moment.

       Example: lash sched run "help" 0 0 5 """
    try:
        if h <= 0 and m <= 0 and s <= 0:
            raise Exception('Error: Time delay is not defined')
    except Exception as e:
        print(e)
    t = h * 3600 + m * 60 + s  # Converting to seconds
    sc.every(t).seconds.do(system, command=command)
    while True:
        sc.run_pending()


@sched.command()
@click.argument('command', metavar='command', type=click.STRING)
@click.argument('h', metavar='<hours>', type=click.INT, required=False, default=0)
@click.argument('m', metavar='<minutes>', type=click.INT, required=False, default=0)
@click.argument('s', metavar='<seconds>', type=click.INT, required=False, default=0)
def wait(command, h, m, s):
    """\b
        Wait x time, run a task once and exit
        Example: lash sched wait "help" 0 0 10  """
    # assert h <= 0 and m <= 0 and s <= 0, 'Error: Time delay is not defined'
    t = h * 3600 + m * 60 + s  # Converting to seconds
    for i in range(0, t):
        sleep(1)
        print(f'Time remaining: {(t - i) // 60 // 60}h {(t - i) // 60}m {t - i}s ', end="\r")
    sleep(1)
    print(f'Time remaining: 0h 0m 0s ', end="\r")
    try:
        playbp()
    except:
        pass
    system(command=command)


@sched.command()
@click.argument('time', metavar='time', type=click.STRING)
@click.argument('command', metavar='<command>', type=click.STRING)
def exec(time, command):
    """\b
        Execute a task from determined moment of day
        \b
        The time need to have this syntax: 10:30:0
        Command example exec 10:30:0 "help"
    """
    if not search('\d\d:\d\d:\d', time):
        return print('ERROR sytax incorrect, try use 10:30:0 with time')
    while True:
        if f'{datetime.now().hour}:{datetime.now().minute}:{datetime.now().second}' == time:
            try:
                playbp()
            except:
                pass
            system(command=command)
            return
        else:
            print(f'Waiting {time} -> {datetime.now().hour}:{datetime.now().minute}:{datetime.now().second}', end='\r')

