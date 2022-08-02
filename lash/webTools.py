import click
import os
from lash.Exportables.config import config
import requests as r
import bs4
from rich.console import Console
from rich.table import Table


config = config()


@click.group('web', help='Web-Tools')
def web():
    ...


@web.command()
@click.argument('path', metavar='<destiny>', type=click.Path(exists=True), default='.', required=False)
def new(path):
    """Start a new web project

    \b
    This command will create html5, css and javascript files in the destination folder
    You can also edit the files code in the config.py file, to find the location of this
    archive use the lash getconfig command, in the file, you will receive more instructions
    """
    os.chdir(path)
    with open('index.html', 'w') as index:
        index.write(config['html_code'])
        index.close()
    with open('style.css', 'w') as style:
        style.write(config['css_code'])
        style.close()
    with open('script.js', 'w') as script:
        script.write(config['js_code'])
        script.close()
    print('Files Created')


@web.command(help='Scrape a Github profile')
@click.argument('user_name', metavar='<nick>', type=click.STRING)
@click.option('-op', is_flag=True, help='Open the user page on browser')
def ghscrape(user_name, op):
    try:
        url = f'https://github.com/{user_name}'
        github = bs4.BeautifulSoup(r.get(url).text, 'html.parser')
        all = github.find_all('rect', 'ContributionCalendar-day')
        if len(all) == 0:
            print('Error, profile not found')
            return
        week = ''
        del all[-5:-1]
        del all[:-8]
        all.pop()

        data_level = list()
        data_date = list()
        for e in all:
            data_level.append(e['data-level'])
            data_date.append(e['data-date'])
        gh = {
            'nick': github.find('span', 'p-nickname vcard-username d-block').text.strip(),
            'contributions': github.find('h2', 'f4 text-normal mb-2').text.strip()[0:4].replace('\n', ''),
            'followers': github.find('span', 'text-bold color-fg-default').text.strip(),
            'repos': github.find('span', 'Counter').text.strip(),
            'bio': github.find('div', 'p-note user-profile-bio mb-3 js-user-profile-bio f4').text.strip()
        }
        if len(gh['bio']) > 60:
            gh['bio'] = gh['bio'][:60]
            gh['bio'] += '...'
        print(f"""
UsrInf :: {gh['nick']} -> {gh['contributions']} contributions, {gh['followers']} followers, {gh['repos']} repos
UsrBio :: {gh['bio']}\n""")

        table = Table(title="User activity")

        table.add_column(f"Date", style="cyan")
        table.add_column(f"Activity", style="green")

        for (date, val) in zip(data_date, data_level):
            table.add_row(date, val)

        Console().print(table)

        if op:
            click.launch(url)
    except Exception as e:
        print(e)


@web.command(help='Send a email easy')
@click.option('-email', prompt=True)
@click.option('-passw', prompt=True, hide_input=True)
def mail(email, passw):
    print(email, passw)

