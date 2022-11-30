import click
from random import sample, randint

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
