import click
from random import randint

from rich.table import Table

from lash.Exportables.config import config
from lash.executor import abs_path_config
from os import system, name
from random import sample, randint


config = config()


@click.command(help='Get the config.py path')
def getConfig():
    print(f'\n[ {abs_path_config()} ]')


@click.command(help='Generate random sequences')
@click.option('-c', type=click.INT, default=5, show_default=True, help='Number of characters in random output')
@click.option('-n', is_flag=True, help='Enable numbers', default=True, show_default=True)
@click.option('-l', is_flag=True, help='Enable letters', default=False, show_default=True)
@click.option('-s', is_flag=True, help='Enable special characters', default=False, show_default=True)
@click.option('-ul', is_flag=True, help='Enable Uppers and lowers for letters', default=False, show_default=True)
def random(c, n, l, s, ul):
    rand_l = []
    if n:
        rand_l.append('123456789')
    if l:
        letters = 'qwertyuiopasdfghjklzxcvbnm'
        if ul:
            for letter in letters:
                if randint(0, 1) == 1:
                    letter = letter.upper()
                rand_l.append(letter)
        else:
            rand_l.append(letters)
    if s:
        rand_l.append('!?@#$%&*')
    if len(rand_l) > 0:
        try:
            print(''.join(sample(''.join(rand_l), c)))
        except ValueError:
            print('Error: Number of characters exceeded the total, reduce the -c value')
    else:
        print('Error: Please enable something to be randomized')


@click.command()
def taskkiller():
    """\b
        Kill multiple processes with single command

        \b
        This command is automation to close processes, to use it, you need
        to put the process names in the configuration file so that they
        can be processed one by one by the function.
        \b
        You can find the file in the package's installation folder, in the path
        lash/Exportables/config.py, there you will have instructions on how to use it.
    """
    if len(config['black_list']) == 0:
        print(f"""
- None process name funded on <black_list> value
To use this command correctly, you need add the processes names manually in\n[{abs_path_config()}]
To more details use --help option
    """)
    if name == 'nt':
        for p in config['black_list']:
            system(f'taskkill /F /IM {p} /T') if name == 'nt' else system(f'pkill {p}')
    else:
        ...
    print('\n<FUNCTION END>')


import psutil as ps
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich import print
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
import time


@click.command()
def manege():
    job_progress = Progress(
        "{task.description}",
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    )
    progress_table = Table.grid(expand=True)
    progress_table.add_row(
        Panel(job_progress, title="[b]Jobs", border_style="red", padding=(1, 2)),
    )
    job_progress.add_task("[cyan]Mixing", total=1000)
    job_progress.add_task("[green]lowrin", total=2000)
    job_progress.add_task("[green]lowrin", total=2000)
    layout = Layout()
    layout.split_column(
        Layout(name='header'),
        Layout(name='main'),
        Layout(name='footer')
    )
    """ layout['main'].split_row(
        Panel(f"{job_progress}", title="Welcome", subtitle="Thank you", style='cyan'),
        Panel("Hello, [red]World!", title="Welcome", subtitle="Thank you", style='cyan')
    )"""
    layout['main'].update(progress_table)
    with Live(layout, refresh_per_second=10):
        while True:
            time.sleep(0.00001)
            for job in job_progress.tasks:
                if not job.finished:
                    job_progress.advance(job.id)


