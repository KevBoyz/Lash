import click, schedule as sc
from os import system


@click.group('sched', help='Schedule tasks at the command line level')
def sched():
    pass


@sched.command(help='Run a task')
def run():
    sc.every(2).seconds.do(system, command=r'python C:\Users\Kevin\Documents\GitHub\Lash\__init__.py random ')
    while True:
        sc.run_pending()