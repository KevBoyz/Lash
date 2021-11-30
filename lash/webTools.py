import click
import os
from lash.Exportables.config import config
import requests as r
import bs4


config = config()


@click.group('web', help='Web-Tools')
def web():
    ...


@web.command()
@click.argument('path', metavar='<destiny>', type=click.Path(exists=True), default='.', required=False)
def new(path):
    '''Start a new web project

    \b
    This command will create html5, css3 and javascript files in the destination folder
    You can also edit the files code in the config.py file, to find the location of this
    archive use the getConfig, in the file, you will receive more instructions
    '''
    os.chdir(path)
    index = open('index.html', 'w')
    index.write(config['html_code'])
    index.close()
    print('Files Generated')


@web.command(help='Scrape a Github profile')
@click.argument('user_name', metavar='<nick>', type=click.STRING)
def ghscrape(user_name):
    try:
        github = bs4.BeautifulSoup(r.get(f'https://github.com/{user_name}').text, 'html.parser')
        all = github.find_all('rect', 'ContributionCalendar-day')
        if len(all) == 0:
            print('Error, profile not found')
            return
        week = ''
        del all[-5:-1]
        del all[:-8]
        all.pop()
        for e in all:
            week += e['data-level'] + ' '
        gh = {
            'nick': github.find('span', 'p-nickname vcard-username d-block').text.strip(),
            'contributions': github.find('h2', 'f4 text-normal mb-2').text.strip()[0:4].replace('\n', ''),
            'followers': github.find('span', 'text-bold color-fg-default').text.strip(),
            '7days': week
        }
        print(f"""
    Github :: {gh['nick']} -> {gh['contributions']} contributions, {gh['followers']} followers
    Github :: Last 7 days commits, (7-1): {gh['7days']}""")
    except Exception as e:
        print(e)

