from itertools import chain, product
from random import sample
from string import ascii_letters, digits, punctuation, whitespace


def _charset_size(letters, numbers, symbols, spaces):
    size = 0
    size += len(ascii_letters) if letters else 0
    size += len(digits) if numbers else 0
    size += len(punctuation) if symbols else 0
    size += len(whitespace) if spaces else 0
    return size


def total_combinations(length, ramp, letters, numbers, symbols, spaces, start_length=1):
    size = _charset_size(letters, numbers, symbols, spaces)
    if size == 0:
        return 0
    if ramp:
        if start_length < 1 or start_length > length:
            start_length = 1
        return sum(size ** i for i in range(start_length, length + 1))
    return size ** length


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
