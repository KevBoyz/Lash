import click
import pandas as pd
import os
import json
from matplotlib import pyplot as plt
from matplotlib import set_loglevel
from datetime import datetime
from typing import List, Tuple, NoReturn


def time_format(*args: int) -> List:
    """
    Take an int and format it to time display:
    1 -> 01, 7 -> 07, 12 -> 12
    """
    fmt = list(map(lambda x:
                         '0' + str(x) if len(str(x)) == 1
                         else str(x), args))
    return fmt

def time_conversor(s: float) -> Tuple[str, float]:
    """
    Take seconds, and return it in h:m:s format.

    x seconds -> 00:05:12

    ntime is hours.minutes like:
    h = 2, m = 10 -> 2.1

    ntime is used to make a groupby using
    pandas when -a are inputted. This will be
    saved on a csv database.
    """
    h = int(s / 3600)
    tm = int(s / 60)  # Total minutes
    m = int(s / 60) - h * 60  # Rest
    s = int(s - tm * 60)
    if len(str(m)) == 1:  # Equivalent to m/10
        ntime = float(f'{h}.0{m}')
    else:
        ntime = float(f'{h}.{m}')
    h, m, s = time_format(h, m, s)
    return f'{h}:{m}:{s}', ntime


def make_files(s, cache:str, csv:str) -> NoReturn:
    """
    Create files for data storing.
    """
    if s:  # s is a flag
        with open(cache, 'w'):
            pass  # Create the file
    if not os.path.exists('work.csv'):
        with open(csv, 'w') as file:
            file.write('date,time,message\n')


def del_cache(cache: str) -> NoReturn:
    """
    Delete cache file after the save data in csv.
    """
    os.remove(cache)


def analyze(workcsv: str) -> NoReturn:
    """
    This command reads a csv and plot the data
    on a pyplot graph (cyberpunk style).
    """
    set_loglevel('error')  # Hide terminal warnings
    df = pd.read_csv(workcsv)
    df = df.drop(columns=['message'], axis=1)
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
    plt.ylabel('Time (hours.minutes)')

    plt.plot(fdf, color='#00ff41', marker='o')
    plt.show()


@click.command(short_help='Manage your work time')
@click.option('-s', is_flag=True, help='Start working')
@click.option('-e', is_flag=True, help='End work')
@click.option('-m', type=click.STRING, help='Add message')
@click.option('-sv', is_flag=True, default=True, show_default=True, help='Save data')
@click.option('-a', is_flag=True, help='Plot your worktime')
def work(s, e, m, sv, a):
    """
    This command compute how much time you work and save it.

    \b
    Start your journey using -s and end with -e.
    The final time will be saved in a .csv file, but
    if you don't want to save, use -e with -sv.

    \b
    To save the time with a note, use -m [message]

    \b
    The work.csv will be created in the actual directory of the terminal.
    Other file named cache.json are created to, and it saves the time
    you start your work. After save data on csv, this file is deleted.

    - To maintain the data, be sure to always perform this in the same folder.
    """
    cache = 'cache.json'
    workcsv = 'work.csv'
    make_files(s, cache, workcsv)
    now = datetime.now()
    if not m:
        m = 'unknown'
    if s:
        json_time = {'year': now.year, 'month': now.month,
                  'day': now.day, 'hour': now.hour, 'minute': now.minute}
        with open(cache, 'w') as file:
            file.write(json.dumps(json_time))
        hr, _min, sec = time_format(json_time["hour"], json_time["minute"], now.second)
        print(f'Starting at {hr}:{_min}:{sec}')
    elif e:
        with open(cache, 'r') as file:
            try:
                time = json.loads(file.read())
            except json.JSONDecodeError:
                print('Error: Cache empty or can\' be readied.'
                      'Be sure that you use [command -s] before run this')
        date_time = datetime(time['year'], time['month'],
                time['day'], time['hour'], time['minute'])
        delta = now - date_time
        date = date_time.date()
        time, ntime = time_conversor(delta.total_seconds())
        print(f'Time worked: {time}')
        if sv:
            csv = pd.read_csv(workcsv)
            csv.loc[len(csv.index)] = [date, ntime, m]
            with open(workcsv, 'w') as file:
               file.write(csv.to_csv(index=False))
            del_cache(cache)
    elif a:
        analyze(workcsv)
