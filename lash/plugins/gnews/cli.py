import click
from gnews import GNews
from lash.plugins.gnews.core import impress_news


@click.command(short_help="See the last news (Google News)")
@click.option("-t", is_flag=True, default=True, show_default=True, help="Main news")
@click.option("-c", type=click.STRING, help="Main news of a country")
@click.option("-s", type=click.STRING, help="Search news")
@click.option("-tp", type=click.STRING, help="News per topic")
@click.option(
    "-lang", type=click.STRING, default="pt", show_default=True, help="News language"
)
@click.option(
    "-cont", type=click.STRING, default="BR", show_default=True, help="Your country"
)
def gnews(t, c, s, tp, lang, cont):
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
