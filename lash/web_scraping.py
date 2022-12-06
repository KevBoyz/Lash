import click
import os
import bs4
import requests as r
import pathlib
import wikipedia as wk
from pytube import YouTube
from gnews import GNews
from tqdm import tqdm
from rich import print
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from lash.Exportables.webTools import *

downloads_folder = os.path.join(pathlib.Path.home(), 'Downloads')


@click.group('web', help='scraping tools')
def web():
    ...


@web.command(help='Scrape a Github profile')
@click.argument('user_name', metavar='<nick>', type=click.STRING)
@click.option('-op', is_flag=True, help='Open the user page on browser')
def gith(user_name, op):
    try:
        url = f'https://github.com/{user_name}'
        github = bs4.BeautifulSoup(r.get(url).text, 'html.parser')
        all = github.find_all('rect', 'ContributionCalendar-day')
        if len(all) == 0:
            print('Error, profile not found')
            return
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
UsrInf :: [bold green]{gh['nick']}[/bold green] -> {gh['contributions']} contributions, {gh['followers']} followers, {gh['repos']} repos
UsrBio :: [italic]{gh['bio']}[/italic]\n""")
        table = Table(title="User activity")
        table.add_column(f"Date", style="cyan", justify='center')
        table.add_column(f"Level", style="green", justify='left')
        for (date, val) in zip(data_date, data_level):
            val_bar = ''
            for _ in range(0, int(val)):
                val_bar += '■ '
            table.add_row(date, val_bar.strip())
        Console().print(table)
        if op:
            click.launch(url)
    except Exception as e:
        print(e)


@web.command(help='Send a email easy')
@click.option('-email', prompt=True)
@click.option('-passw', prompt=True, hide_input=True)
@click.option('-to', prompt=True)
@click.option('-subject', prompt=True)
@click.option('-message', prompt=True)
def mail(email, passw, to, subject, message):
    from mailer import Mailer
    try:
        mail = Mailer(email=email, password=passw)
        mail.send(receiver=to, subject=subject, message=message)
        print('[green]Your email has been sent[/green]')
    except Exception as e:
        print(f'{e}')


@web.command(help='download Youtube video/audio')
@click.option('-l', type=click.STRING, help='video link')
@click.option('-s', type=click.STRING, help='catch video searching')
@click.option('-a', is_flag=True, help='audio only')
@click.option('-f', type=click.Path(), default=downloads_folder, show_default=True, help='output folder')
@click.option('-low', is_flag=True, help='low resolution')
@click.option('-list', type=click.Path(exists=True), help='Search multiple videos')
def yt(l, s, a, f, low, list):
    if not list:
        def on_progress(vid, chunk, bytes_remaining):
            totalsz = round((vid.filesize / 1024) / 1024, 1)
            remain = round((bytes_remaining / 1024) / 1024, 1)
            p_bar.reset()
            p_bar.update(int(totalsz - remain))
            p_bar.refresh()
        global p_bar
        print('Getting video', end='')
        if l and not a:
            yt = YouTube(l, on_progress_callback=on_progress)
            video, totalsz = get_video_by_link(yt, low)
            p_bar = tqdm(range(int(totalsz)), colour='green')
            video.download(f)
        elif a:
            if l:
                yt = YouTube(l, on_progress_callback=on_progress)
                video, totalsz = get_audio_by_link(yt)
                p_bar = tqdm(range(int(totalsz)), colour='green')
            elif s:
                video = get_audio_by_search(s)
            out_file = video.download(output_path=f)
            base, ext = os.path.splitext(out_file)
            new_file = base + '.mp3'
            os.rename(out_file, new_file)
        elif s and not l:
            if low:
                video = get_video_by_search(s, low)
            else:
                video = get_video_by_search(s)
            video.download(f)
            print('Download complete')
    elif list:
        c = 0
        with open(list, 'r') as file:
            for line in file.readlines():
                c += 1
                print(f'{c} Getting video', end='')
                if a:
                    video = get_audio_by_search(line)
                    out_file = video.download(output_path=f)
                    base, ext = os.path.splitext(out_file)
                    new_file = base + '.mp3'
                    os.rename(out_file, new_file)
                else:
                    if low:
                        video = get_video_by_search(line, low)
                    else:
                        video = get_video_by_search(line)
                    video.download(f)
                print('[Download complete]')
        print('All downloads complete')



@web.command(help='Read articles of wikipedia')
@click.option('-p', type=click.STRING, help='Get a page by title')
@click.option('-lang', type=click.STRING, default='pt', show_default=True, help='Article language')
@click.option('-f', is_flag=True, default=False, show_default=True, help='View full article')
def wiki(p, lang, f):
    wk.set_lang(lang)
    if not f:
        summary = Text(wk.summary(p), justify='left')
        print(Panel(summary, title=f'{p} - Summary'))
    elif f:
        page = wk.page(p)
        article = Text(page.content, justify='left')
        print(Panel(article, title=page.title))


@web.command(help='See the last news (Google news)')
@click.option('-t', is_flag=True, help='Top news')
@click.option('-c', type=click.STRING, help='Top news of a country')
@click.option('-s', type=click.STRING, help='Search news')
@click.option('-tp', type=click.STRING, help='News per topic: [WORLD TECHNOLOGY SCIENCE BUSINESS NATION SPORTS HEALTH ENTERTAINMENT')
@click.option('-lang', type=click.STRING, default='pt', show_default=True, help='News language')
@click.option('-cont', type=click.STRING, default='BR', show_default=True, help='News country')
def news(t, c, s, tp, lang, cont):
    gn = GNews(language=lang, country=cont)
    if t:
        top_news = gn.get_top_news()
        impress_news(top_news)
    elif c:
        county_news = gn.get_news_by_location(c)
        impress_news(county_news)
    elif s:
        kw_news = gn.get_news(s)
        impress_news(kw_news)
    elif tp:
        topic_news = gn.get_news_by_topic(tp)
        impress_news(topic_news)
