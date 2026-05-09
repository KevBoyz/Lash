import os
from matplotlib import pyplot as plt, set_loglevel
from typing import List, Tuple, NoReturn


def time_format(*args: int) -> List:
    fmt = list(map(lambda x:
                   '0' + str(x) if len(str(x)) == 1
                   else str(x), args))
    return fmt


def time_conversor(s: float) -> Tuple[str, int]:
    h = int(s / 3600)
    total_minutes = int(s / 60)
    m = int(s / 60) - h * 60
    s = int(s - total_minutes * 60)
    h, m, s = time_format(h, m, s)
    return f'{h}:{m}:{s}', total_minutes


def make_files(s, cache: str, csv: str) -> NoReturn:
    if s:
        with open(cache, 'w'):
            pass
    if not os.path.exists('work.csv'):
        with open(csv, 'w') as file:
            file.write('date,time,message\n')


def del_cache(cache: str) -> NoReturn:
    os.remove(cache)


def analyze(workcsv: str) -> NoReturn:
    import pandas as pd
    set_loglevel('error')
    df = pd.read_csv(workcsv)
    df = df.drop(columns=['message'], axis=1)
    df = df.drop(columns=['real_time'], axis=1)
    fdf = df.groupby(['date']).sum()
    plt.style.use('seaborn-dark')

    for param in ['figure.facecolor', 'axes.facecolor', 'savefig.facecolor']:
        plt.rcParams[param] = '#212946'

    for param in ['text.color', 'axes.labelcolor', 'xtick.color', 'ytick.color']:
        plt.rcParams[param] = '0.9'

    fig, ax = plt.subplots()
    ax.grid(color='#2B4969')

    plt.title('Work time')
    plt.xlabel('Date')
    plt.ylabel('Minutes')

    plt.plot(fdf, color='#00ff41', marker='o')
    plt.show()
