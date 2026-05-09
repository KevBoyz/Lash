import os
import click
import zipfile
from itertools import count
from lash.plugins.crack.core import brute, _next
from lash.plugins.crack.helpers import path_no_file


@click.group('crack', short_help='Use the brute force')
def crack():
    """
    Set of commands to crack passwords
    """
    ...


@crack.command(short_help='Crack a zipfile')
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.option('-ln', type=click.INT, default=10, show_default=True, help='Maximum length')
@click.option('-r', is_flag=True, default=True, show_default=True, help='Disable ramp')
@click.option('-n', is_flag=True, default=False, show_default=True, help='Enable numbers')
@click.option('-l', is_flag=True, default=True, show_default=True, help='Disable letters')
@click.option('-s', is_flag=True, default=False, show_default=True, help='Enable symbols')
@click.option('-sp', is_flag=True, default=False, show_default=True, help='Enable spaces')
def azip(path, ln, r, n, l, s, sp):
    os.chdir(path_no_file(path))
    attempts = count(0, 1)
    permutations = brute(ln, r, l, n, s, sp)
    zip_arch = zipfile.ZipFile(path)
    while True:
        try:
            nx = _next(permutations)
            pm = bytes(nx, encoding='utf-8')
            try:
                zip_arch.extractall(pwd=pm)
                print(f'\nPassword is: {nx}')
                break
            except:
                print(f'Password attempts: {next(attempts)} Trying: {nx}', end='\r')
        except StopIteration:
            print('Password not found')
            break
