import click
from random import sample, randint
from time import sleep
from datetime import datetime

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


import psutil

def getListOfProcessSortedByMemory():
    listOfProcObjects = []
    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict(attrs=['pid', 'name', 'username'])
            pinfo['vms'] = proc.memory_info().vms / (1024 * 1024)
            listOfProcObjects.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    # Sort list of dict by key vms i.e. memory usage
    listOfProcObjects = sorted(listOfProcObjects, key=lambda procObj: procObj['vms'], reverse=True)
    return listOfProcObjects


import psutil as ps
from dashing import *


@click.command(help='System panel')
def monitor():
    tui = HSplit(
        VSplit(
            VGauge(val=100, title='Ram Usage', border_color=2),
            VGauge(val=100, title='Disk Space', border_color=2)
        ),
        VSplit(
            HGauge(val=100, title='Cpu Usage - x%', border_color=2),
            HChart(val=100, title='Cpu graph', border_color=2, color=2)
        ),
        VSplit(
            Text('Getting information...', border_color=2, title='Machine config', color=2),
            Log('logs', border_color=2, color=2, title='Processes with highest memory usage')

        ),
    )
    cpu_percent = tui.items[1].items[0]
    cpu_graph = tui.items[1].items[1]
    ram_percent = tui.items[0].items[0]
    disk_percent = tui.items[0].items[1]

    machine_config = tui.items[2].items[0]
    processes = tui.items[2].items[1]

    while True:
        cpu_perc = ps.cpu_percent(1)
        vmomory = ps.virtual_memory()
        disk = ps.disk_usage('.')

        cpu_percent.value = cpu_perc
        cpu_percent.title = f'Cpu Usage - {cpu_perc}%'

        cpu_graph.append(cpu_perc)

        ram_percent.value = vmomory.percent
        ram_percent.title = f'Ram Usage - {vmomory.percent}%'

        disk_percent.value = disk.percent
        disk_percent.title = f'Disk Usage - {disk.percent}%'

        machine_config.text = f'Cpu freq: {ps.cpu_freq().current / 1000}Ghz Max({ps.cpu_freq().max / 1000}Ghz)\n' \
                              f'Cpu nucleus: {ps.cpu_count(logical=False)} Cpu threads: {ps.cpu_count(logical=True)}\n' \
                              f'Cpu times: User({ps.cpu_times().user / 60 / 60:.2f}h) Sys({ps.cpu_times().system / 60 / 60:.2f}h)\n' \
                              f'Booted since {datetime.fromtimestamp(ps.boot_time()).strftime("%Y-%m-%d %H:%M:%S")}\n' \
                              f'Ram: {vmomory.total /1024/1024/1024:.2f}Gb | Using {vmomory.used /1024/1024/1024:.2f}Gb\n' \
                              f'Disk: {disk.total/1024/1024/1024:.2f}Gb | Using {disk.used/1024/1024/1024:.2f}Gb\n'
        try:
            listOfProcessNames = list()
            for proc in psutil.process_iter():
                pInfoDict = proc.as_dict(attrs=['pid', 'name', 'cpu_percent'])
                listOfProcessNames.append(pInfoDict)
            listOfRunningProcess = getListOfProcessSortedByMemory()
            for elem in listOfRunningProcess[:11]:
                processes.append(f'{elem["name"]}|{elem["pid"]}|{elem["vms"]:.2f}mb')
        except:
            pass

        tui.display()
        sleep(.1)


from lash.executor import abs_path_data
import pandas as pd
import os
import json
from matplotlib import pyplot as plt
from matplotlib import set_loglevel

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
