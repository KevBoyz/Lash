import click
import os
import bs4
import requests as r
import pathlib
import wikipedia as wk
from gnews import GNews
from rich import print
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from lash.plugins.web.core import download_yt, impress_news

downloads_folder = os.path.join(pathlib.Path.home(), 'Downloads')


@click.group('web', help='Scraping tools')
def web():
    ...


@web.command(short_help='Scrape a Github profile')
@click.argument('nick', type=click.STRING)
@click.option('-op', is_flag=True, help='Open the user page on browser')
def gith(nick, op):
    """
    \b
    This command going to scrape github.com/NICK and take:
    Activity, followers, repositories and bio.
    """
    try:
        api_resp = r.get(
            f'https://api.github.com/users/{nick}',
            headers={'Accept': 'application/vnd.github.v3+json'}
        )
        if api_resp.status_code != 200:
            print('Error, profile not found')
            return
        data = api_resp.json()

        contrib_resp = r.get(
            f'https://github.com/users/{nick}/contributions',
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        contrib_soup = bs4.BeautifulSoup(contrib_resp.text, 'html.parser')

        contrib_h2 = contrib_soup.find('h2', 'f4 text-normal mb-2')
        contributions = contrib_h2.text.split()[0] if contrib_h2 else 'N/A'

        days = contrib_soup.find_all('td', 'ContributionCalendar-day')
        recent = days[-7:] if len(days) >= 7 else days

        bio = data.get('bio') or ''
        if len(bio) > 60:
            bio = bio[:60] + '...'

        url = f'https://github.com/{nick}'
        print(
            f"\nUsrInf :: [bold green]{data['login']}[/bold green]"
            f" -> {contributions} contributions,"
            f" {data['followers']} followers, {data['public_repos']} repos\n"
            f"UsrBio :: [italic]{bio}[/italic]\n"
        )
        table = Table(title="User activity")
        table.add_column("Date", style="cyan", justify='center')
        table.add_column("Level", style="green", justify='left')
        for day in recent:
            date = day.get('data-date', '')
            level = day.get('data-level', '0')
            table.add_row(date, ('■ ' * int(level)).strip())
        Console().print(table)
        if op:
            click.launch(url)
    except Exception as e:
        print(e)


@web.command(short_help='Read articles of wikipedia')
@click.option('-t', type=click.STRING, help='The title of the article')
@click.option('-lang', type=click.STRING, default='pt', show_default=True, help='Article language')
@click.option('-f', is_flag=True, default=False, show_default=True, help='View full article')
def wiki(t, lang, f):
    """
    Read articles of Wikipedia

    - The default of this command is returns only the summary. Use -f for full.
    - To change the language use -lang and pass a language code.
    """
    wk.set_lang(lang)
    if not f:
        summary = Text(wk.summary(t), justify='left')
        print(Panel(summary, title=f'{t} - Summary'))
    elif f:
        page = wk.page(t)
        article = Text(page.content, justify='left')
        print(Panel(article, title=page.title))


@web.command(short_help='Download Youtube video/audio')
@click.option('-l', 'link', type=click.STRING, help='Video link')
@click.option('-s', type=click.STRING, help='Video name (for search)')
@click.option('-a', is_flag=True, help='Audio only')
@click.option('-f', type=click.Path(), default=downloads_folder, show_default=True, help='output folder')
@click.option('-low', is_flag=True, help='Low resolution (video only)')
@click.option('-file', type=click.Path(exists=True), help='Download multiple videos listed on a text file')
def yt(link, s, a, f, low, file):
    """
    This command allows you download videos/audios from Youtube.

    \b
    There are two SIMPLE MANNERS to find your video:
        -l: Paste the video link. This method is more confident.
        -s: Type the video name. The name will be used to search
            for the video. It will use the first result.

    \b
    If you want to AUTOMATE the download process of multiple videos,
    you can create a text file and write the video(s) name(s)/link(s)
    (one for each line). Pass the path of the file using the -file option.

    \b
    For a FAST download you can use -low flag. This will return
    the lowest resolution of the video. The default of this command
    is return the highest resolution.

    \b
    To download only the AUDIO of the video, use the flag -a.
    The download will return a .mp3 file (requires ffmpeg).
    """
    if not file:
        query = link or s
        if not query:
            print('Provide -l (link) or -s (search term)')
            return
        title = download_yt(query, f, low=low, audio_only=a)
        print(f'Download complete: {title}')
    else:
        c = 0
        with open(file, 'r') as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                c += 1
                print(f'[{c}] Downloading...')
                title = download_yt(line, f, low=low, audio_only=a)
                print(f'[{c}] Done: {title}')
        print(f'All {c} downloads complete')


@web.command(short_help='See the last news (Google News)')
@click.option('-t', is_flag=True, default=True, show_default=True, help='Main news')
@click.option('-c', type=click.STRING, help='Main news of a country')
@click.option('-s', type=click.STRING, help='Search news')
@click.option('-tp', type=click.STRING, help='News per topic')
@click.option('-lang', type=click.STRING, default='pt', show_default=True, help='News language')
@click.option('-cont', type=click.STRING, default='BR', show_default=True, help='Your country')
def news(t, c, s, tp, lang, cont):
    """
    This command scrape news from Google News.

    \b
    -c: Filter news for a country. Example: Brazil, Pakistan.
    -s: Search for a something you want. Return the top news.

    \b
    To filter news by topic use -tp. Topics available:
       - WORLD TECHNOLOGY SCIENCE BUSINESS NATION SPORTS HEALTH ENTERTAINMENT
    It is necessary to pass your topic in high-case, like as shown above.

    \b
    - To change the LANGUAGE use -lang and pass a language code.
    - To change your COUNTRY use -cont and pass a country code.

    \b
    * In case of SLOWNESS:
        Reset your ip address: Your IP may have been moved to a blacklist.
    """
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
