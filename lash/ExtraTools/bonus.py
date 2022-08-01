import click
from lash.Exportables.config import config
from lash.executor import abs_path_config
from os import system, name
from random import sample, randint
from time import sleep
import datetime

config = config()


@click.command(help='Get the config.py path')
def getConfig():
    print(f'\n[ {abs_path_config()} ]')


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


@click.command()
def taskkiller():
    """\b
        Kill multiple processes with single command

        \b
        This command is automation to close processes, to use it, you need
        to put the process names in the configuration file so that they
        can be processed one by one by the function.
        \b
        You can find the file in the package's installation folder, in the path
        lash/Exportables/config.py, there you will have instructions on how to use it.
    """
    if len(config['black_list']) == 0:
        print(f"""
- None process name funded on <black_list> value
To use this command correctly, you need add the processes names manually in\n[{abs_path_config()}]
To more details use --help option
    """)
    if name == 'nt':
        for p in config['black_list']:
            system(f'taskkill /F /IM {p} /T') if name == 'nt' else system(f'pkill {p}')
    else:
        ...
    print('\n<FUNCTION END>')


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
                              f'Booted since {datetime.datetime.fromtimestamp(ps.boot_time()).strftime("%Y-%m-%d %H:%M:%S")}\n' \
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
