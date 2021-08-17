import click, schedule as sc
from os import system
from time import sleep
from lash.executor import playbp


@click.group('sched', help='Schedule tasks at the command line level')
def sched():
    pass


@sched.command()
@click.argument('command', metavar='command', type=click.STRING)
@click.option('-s', type=click.INT, help='Set delay seconds')
@click.option('-m', type=click.INT, help='Set delay minutes')
@click.option('-h', type=click.INT, help='Set delay hours')
def run(command, s, m, h):
    """\b
       Run commands repetitively at a given interval starting from
       current moment.

       Example: lash sched run -s 10 "help" """
    if not s and not m and not h:
        raise Exception('Error, time delay is not defined')
    if s and m and h or s and m or s and h or h and m:
        raise Exception('Error, not support for multi time options')
    else:
        sc.every(s).seconds.do(system, command=command) if s else None
        sc.every(m).minutes.do(system, command=command) if m else None
        sc.every(h).hours.do(system, command=command) if h else None
        while True:
            sc.run_pending()


@sched.command()
@click.argument('command', metavar='command', type=click.STRING)
@click.argument('h', metavar='hours', type=click.INT, required=False, default=0)
@click.argument('m', metavar='minutes', type=click.INT, required=False, default=0)
@click.argument('s', metavar='seconds', type=click.INT, required=False, default=0)
def wait(command, h, m, s):
    """\b
           Wait x time, run a task once and exit
           Example: lash sched wait "help" 0 0 10  """
    assert h >= 0 and m >= 0 and s >= 0, 'Error: Time delay is not defined'
    t = h * 3600 + m * 60 + s  # Converting to seconds
    for i in range(0, t):
        sleep(1)
        print(f'Time remaining: {(t - i) // 60 // 60}h {(t - i) // 60}m {t - i}s ', end="\r")
    sleep(1)
    print(f'Time remaining: 0h 0m 0s ', end="\r")
    playbp()
    system(command=command)

