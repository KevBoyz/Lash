import click
from random import randint
from lash.Exportables.config import config
from os import system, name

config = config()


@click.command(help='Randomize numbers')
@click.option('-s', type=click.INT, default=0, help='Randomization start number')
@click.option('-e', type=click.INT, default=9, help='Randomization end number')
@click.option('-c', type=click.INT, default=5, help='Number of characters in random output')
@click.option('-nl', is_flag=True, help='show to numbers left to randomize')
def random(s, e, c, nl):
    if s != 0:
        e = s + 9
    randstr = ''
    for r in range(0, c):
        randstr += str((randint(s, e)))
        if nl:
            print(f'Numbers left: {c - (r + 1)}', end='\r')
    if len(randstr) > c:
        click.echo(randstr[0:c + 1])
    else:
        click.echo(randstr)


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
        print("""
    - None process find in <black_list>
    To use this command correctly, you need add processes 
    name manually in [/config.py]. To more information's use --help""")
    if name == 'nt':
        for p in config['black_list']:
            system(f'taskkill /F /IM {p} /T') if name == 'nt' else system(f'pkill {p}')
    else:
        ...
    print('\n<FUNCTION END>')
