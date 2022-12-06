import click
from lash.executor import abs_path_data
import pandas as pd
import os
import json
from matplotlib import pyplot as plt
from matplotlib import set_loglevel
from datetime import datetime


def time_format(h, m, s):
    s = str(s)
    m = str(m)
    h = str(h)
    if len(s) == 1:
        s = '0'+s
    if len(m) == 1:
        m = '0'+m
    if len(h) == 1:
        h = '0'+h
    return h, m, s


def time_conversor(s):
    h = int(s / 3600)
    tm = int(s / 60)  # Total minutes
    m = int(s / 60) - h * 60  # Rest
    s = int(s - tm * 60)
    ntime = float(f'{h}.{m}')
    h, m, s = time_format(h, m, s)
    return f'{h}:{m}:{s}', ntime


def analyze(cust, workcsv):
    set_loglevel('error')  # Hide terminal warnings
    if cust:
        workcsv = cust
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
    plt.ylabel('Hours')

    plt.plot(fdf, color='#00ff41', marker='o')
    plt.show()


@click.command(help='manage your work time')
@click.option('-s', is_flag=True, help='Start working')
@click.option('-e', is_flag=True, help='End work')
@click.option('-m', type=click.STRING, help='Add message')
@click.option('-sv', is_flag=True, default=True, show_default=True, help='Save data')
@click.option('-ex', type=click.Path(exists=True), help='Export data')
@click.option('-cust', type=click.Path(exists=True), help='Custom file for archiving')
@click.option('-a', is_flag=True, help='Plot your worktime')
def work(s, e, m, sv, ex, cust, a):
    cache = os.path.join(abs_path_data(), 'cache.json')
    workcsv = os.path.join(abs_path_data(), 'work.csv')
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
                print('Error: Cache empty or can\' be readied. '
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
            if cust:
                workcsv = cust
            with open(workcsv, 'w') as file:
               file.write(csv.to_csv(index=False))
            # print(f'Data saved ~ {workcsv}')  # Pollutes the terminal
    elif ex:
        with open(workcsv, 'r') as file:
            txt = file.read()
        with open(os.path.join(ex, 'work.csv'), 'w') as file:
            file.write(txt)
    elif a:
        analyze(cust, workcsv)
