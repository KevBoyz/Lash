import click
import psutil as ps
from dashing import HSplit, VSplit, VGauge, HGauge, HChart, Text, Log
from time import sleep
from datetime import datetime
from lash.plugins.monitor.core import getListOfProcessSortedByMemory


@click.command()
def monitor():
    """Real-time TUI dashboard for CPU, RAM, disk, and processes.

    \b
    Displays:
      - CPU usage percentage and historical graph
      - RAM and disk usage
      - Machine info: cores, threads, frequency, boot time
      - Top processes by memory usage

    Press Ctrl+C to exit.
    """
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

        machine_config.text = (
            f'Cpu freq: {ps.cpu_freq().current / 1000}Ghz Max({ps.cpu_freq().max / 1000}Ghz)\n'
            f'Cpu nucleus: {ps.cpu_count(logical=False)} Cpu threads: {ps.cpu_count(logical=True)}\n'
            f'Cpu times: User({ps.cpu_times().user / 60 / 60:.2f}h) Sys({ps.cpu_times().system / 60 / 60:.2f}h)\n'
            f'Booted since {datetime.fromtimestamp(ps.boot_time()).strftime("%Y-%m-%d %H:%M:%S")}\n'
            f'Ram: {vmomory.total /1024/1024/1024:.2f}Gb | Using {vmomory.used /1024/1024/1024:.2f}Gb\n'
            f'Disk: {disk.total/1024/1024/1024:.2f}Gb | Using {disk.used/1024/1024/1024:.2f}Gb\n'
        )
        try:
            listOfProcessNames = list()
            for proc in ps.process_iter():
                pInfoDict = proc.as_dict(attrs=['pid', 'name', 'cpu_percent'])
                listOfProcessNames.append(pInfoDict)
            listOfRunningProcess = getListOfProcessSortedByMemory()
            for elem in listOfRunningProcess[:11]:
                processes.append(f'{elem["name"]}|{elem["pid"]}|{elem["vms"]:.2f}mb')
        except Exception:
            pass
        tui.display()
        sleep(.1)
