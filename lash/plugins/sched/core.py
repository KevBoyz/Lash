from typing import List, Tuple


def reg_crono(h: int, m: int, s: int) -> Tuple[int, int, int]:
    if s > 0:
        s -= 1
    else:
        if m > 0:
            m -= 1
            s = 60
        else:
            if h > 0:
                h -= 1
                m = 60
    return h, m, s


def time_format(*args: int) -> List:
    fmt = list(map(lambda x:
                   '0' + str(x) if len(str(x)) == 1
                   else str(x), args))
    return fmt
