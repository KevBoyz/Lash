from random import sample, randint


def get_size(c, n, l, s):
    m = sum([n, l, s])
    if m == 0:
        return c
    return c // m


def gen_random(size, n, s, l, ul):
    rand_l = []
    letters = 'qwertyuiopasdfghjklzxcvbnm'
    symbols = '!?@#$%&*_+-'
    for _ in range(size):
        if n:
            rand_l.append(str(randint(0, 9)))
        if l:
            letter = ''.join(sample(letters, 1))
            rand_l.append(letter.upper() if ul and randint(0, 1) else letter)
        if s:
            rand_l.append(''.join(sample(symbols, 1)))
    return rand_l


def file_save(random_seq):
    r_name = "".join(sample(['7', '5', '6', '2', '4'], 5))
    fname = f'output{r_name}.txt'
    with open(fname, 'w') as file:
        file.write("".join(random_seq))
    return fname
