import click
import zipfile
from itertools import chain, product, count
from random import sample
from string import ascii_letters, digits, punctuation, whitespace


def brute(length, ramp, letters, numbers, symbols, spaces, start_length=1):
    choices = ''
    choices += ascii_letters if letters else ''
    choices += digits if numbers else ''
    choices += punctuation if symbols else ''
    choices += whitespace if spaces else ''
    choices = ''.join(sample(choices, len(choices)))

    if ramp:
        if start_length < 1 or start_length > length:
            start_length = 1

    return chain.from_iterable(product(choices, repeat=i) for i in range(start_length if ramp else length, length+1))


def _next(gen):
    container = ''
    for val in next(gen):
        container += val
    return container





@click.group('crack', short_help='Use the brute force')
def crack():
    """
    Set of commands to crack passwords
    """
    ...


@crack.command(short_help='Crack a zipfile')
#@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.option('-ln', type=click.INT, default=10, show_default=True, help='Maximum length')
@click.option('-r', is_flag=True, default=True, show_default=True, help='Disable ramp')
@click.option('-n', is_flag=True, default=True, show_default=True, help='Disable numbers')
@click.option('-l', is_flag=True, default=True, show_default=True, help='Disable letters')
@click.option('-s', is_flag=True, default=False, show_default=True, help='Enable symbols')
@click.option('-sp', is_flag=True, default=False, show_default=True, help='Enable spaces')
def azip(ln, r, n, l, s, sp):
    attempts = count(0, 1)
    permutations = brute(ln, r, n, l, s, sp)
    while True:
        try:
            print(f'Password attempts: {next(attempts)} Trying: {_next(permutations)}', end='\r')
        except StopIteration:
            break
