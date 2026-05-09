import click
from lash.plugins.random.core import get_size, gen_random, file_save


@click.command(help='Generate random sequences')
@click.option('-c', type=click.INT, default=5, show_default=True, help='Number of characters')
@click.option('-n', is_flag=True, help='Enable numbers', default=True, show_default=True)
@click.option('-l', is_flag=True, help='Enable letters', default=False, show_default=True)
@click.option('-s', is_flag=True, help='Enable special characters', default=False, show_default=True)
@click.option('-ul', is_flag=True, help='Enable Uppers and lowers for letters', default=False, show_default=True)
@click.option('-f', help='Write output on txt file', is_flag=True, default=False, show_default=True)
@click.option('-v', is_flag=True, help='Enable verbose mode', default=False, show_default=True)
def random(c, n, l, s, ul, f, v):
    size = get_size(c, n, l, s)
    random_seq = gen_random(size, n, s, l, ul, v)
    if len(random_seq) < c:
        while len(random_seq) < c:
            random_seq += gen_random(1, n, s, l, ul, v)
    if len(random_seq) > c:
        random_seq = random_seq[:c]
    if f:
        file_save(random_seq)
    else:
        print(f'\n{"".join(random_seq)}\n')
