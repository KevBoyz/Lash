import click
from lash.executor import abs_path_data
import pandas as pd
import os
import json
from matplotlib import pyplot as plt
from matplotlib import set_loglevel
from datetime import datetime


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
    if not m:
        m = 'unknown'
    if s:
        now = datetime.now()
        s_time = {'year': now.year, 'month': now.month,
                  'day': now.day, 'hour': now.hour, 'minute': now.minute}
        with open(cache, 'w') as file:
            file.write(json.dumps(s_time))
        print('Good luck')
    elif e:
        now = datetime.now()
        with open(cache, 'r') as file:
            try:
                time = json.loads(file.read())
            except json.JSONDecodeError:
                print('Error: Cache empty or can\' be readied. '
                      'Be sure that you use [command -s] before run this')
        s_time = datetime(time['year'], time['month'],
                time['day'], time['hour'], time['minute'])
        delta = now - s_time
        date = s_time.date()
        time = f'{delta.total_seconds() / 3600:.2f}'
        csv = pd.read_csv(workcsv)
        csv.loc[len(csv.index)] = [date, time, m]
        print(f'Time worked: {time}h')
        if sv:
            if cust:
                workcsv = cust
            with open(workcsv, 'w') as file:
               file.write(csv.to_csv(index=False))
            print(f'Data saved ~ {workcsv}')
    elif ex:
        with open(workcsv, 'r') as file:
            txt = file.read()
        with open(os.path.join(ex, 'work.csv'), 'w') as file:
            file.write(txt)
    elif a:
        set_loglevel('error')
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
