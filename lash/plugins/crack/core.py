from itertools import chain, product
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

    return \
        chain.from_iterable(product(choices, repeat=i)
                            for i in range(start_length if ramp else length, length + 1))


def _next(gen):
    container = ''
    for val in next(gen):
        container += val
    return container


def get_last(path):
    if path.rfind('\\') != -1:
        last = path[1 + path.rfind('\\'):]
    else:
        last = path[1 + path.rfind('/'):]
    if '"' in last:
        last = last.replace('"', '')
    return last


def path_no_file(path):
    filename = get_last(path)
    return path.replace(filename, '')
