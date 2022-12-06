import click
from random import sample, randint
from tqdm import tqdm


def get_size(c, n, l, s):
    m = 0
    if n:
        m += 1
    if l:
        m += 1
    if s:
        m+= 1
    return c // m

def gen_random(size, n, s, l, ul, v):
    rand_l = []
    letters = 'qwertyuiopasdfghjklzxcvbnm'
    symbols = '!?@#$%&*_+-'
    pbar = None  # To close IDE warning
    if size > 1:
        pbar = tqdm(total=size)
    else:
        v = False
    for c in range(0, size):
        if v:
            pbar.update(1)
        if n:
            rand_l.append(str(randint(0, 9)))
        if l:
            letter = ''.join(sample(letters, 1))
            if ul:
                if randint(0, 1) == 1:
                    rand_l.append(letter.upper())
                else:
                    rand_l.append(letter)
            else:
                rand_l.append(letter)
        if s:
            symbol = ''.join(sample(symbols, 1))
            rand_l.append(symbol)
    return rand_l

def file_save(random_seq):
    r_name = "".join(sample(['7', '5', '6', '2', '4'], 5))
    fname = f'output{r_name}.txt'
    with open(fname, 'w') as file:
        file.write("".join(random_seq))
    print(f'Copied to {fname}')


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
