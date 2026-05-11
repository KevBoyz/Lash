import click
from datetime import datetime
from lash.plugins.work.core import (
    time_format, time_conversor, make_files,
    del_cache, analyze, save_cache, load_cache, save_session,
)


@click.command(short_help='Manage your work time')
@click.option('-s', is_flag=True, help='Start working')
@click.option('-e', is_flag=True, help='End work')
@click.option('-m', type=click.STRING, help='Add message')
@click.option('-sv', is_flag=True, default=False, show_default=True, help='Suppress save')
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
        m = 'none'
    if s:
        json_time = {'year': now.year, 'month': now.month,
                     'day': now.day, 'hour': now.hour, 'minute': now.minute}
        save_cache(cache, json_time)
        hr, _min, sec = time_format(json_time["hour"], json_time["minute"], now.second)
        print(f'Starting at {hr}:{_min}:{sec}')
    elif e:
        cache_time = load_cache(cache)
        date_time = datetime(cache_time['year'], cache_time['month'],
                             cache_time['day'], cache_time['hour'], cache_time['minute'])
        delta = now - date_time
        real_time, total_minutes = time_conversor(delta.total_seconds())
        print(f'Time worked: {real_time}')
        if not sv:
            date = date_time.date()
            save_session(workcsv, date, total_minutes, real_time, m)
            del_cache(cache)
    elif a:
        analyze(workcsv)
