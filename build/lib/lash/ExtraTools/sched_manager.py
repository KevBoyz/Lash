import click, schedule as sc
from os import system


@click.group('sched', help='Schedule tasks at the command line level')
def sched():
    pass


@sched.command()
@click.argument('command', metavar='command', type=click.STRING)
@click.option('-s', type=click.INT, help='Set delay seconds')
@click.option('-m', type=click.INT, help='Set delay minutes')
@click.option('-h', type=click.INT, help='Set delay hours')
def run(command, s, m, h):
    """Run commands repetitively at a given interval starting from
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