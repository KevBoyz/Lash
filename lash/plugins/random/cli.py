import click
from lash.plugins.random.core import get_size, gen_random, file_save


@click.command(help='Generate random sequences')
@click.option('-c', type=click.INT, default=5, show_default=True, help='Number of characters')
@click.option('-n', is_flag=True, help='Enable numbers', default=True, show_default=True)
@click.option('-l', 'letters', is_flag=True, help='Enable letters', default=False, show_default=True)
@click.option('-s', is_flag=True, help='Enable special characters', default=False, show_default=True)
@click.option('-ul', is_flag=True, help='Enable Uppers and lowers for letters', default=False, show_default=True)
@click.option('-f', help='Write output on txt file', is_flag=True, default=False, show_default=True)
def random(c, n, letters, s, ul, f):
    size = get_size(c, n, letters, s)
    random_seq = gen_random(size, n, s, letters, ul)
    if len(random_seq) < c:
        while len(random_seq) < c:
            random_seq += gen_random(1, n, s, letters, ul)
    if len(random_seq) > c:
        random_seq = random_seq[:c]
    if f:
        fname = file_save(random_seq)
        print(f'Saved to {fname}')
    else:
        print(f'\n{"".join(random_seq)}\n')
