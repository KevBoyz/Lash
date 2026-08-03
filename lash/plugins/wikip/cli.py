import click
import wikipedia as wk
from rich import print
from rich.text import Text
from rich.panel import Panel


@click.command(short_help="Read articles of wikipedia")
@click.option("-t", type=click.STRING, help="The title of the article")
@click.option("-lang", type=click.STRING, default="pt",
              show_default=True, help="Article language")
@click.option("-f", is_flag=True, default=False,
              show_default=True, help="View full article")
def wikip(t, lang, f):
    """
    Read articles of Wikipedia

    - The default of this command is returns only the summary. Use -f for full.
    - To change the language use -lang and pass a language code.
    """
    wk.set_lang(lang)
    if not f:
        summary = Text(wk.summary(t), justify="left")
        print(Panel(summary, title=f"{t} - Summary"))
    elif f:
        page = wk.page(t)
        article = Text(page.content, justify="left")
        print(Panel(article, title=page.title))
