import click
import wikipedia as wk
from rich import print
from rich.text import Text
from rich.panel import Panel


@click.command(short_help="Read articles of wikipedia")
@click.argument("title", type=click.STRING)
@click.option("-lang", type=click.STRING, default="pt",
              show_default=True, help="Article language")
@click.option("-f", is_flag=True, default=False,
              show_default=True, help="View full article")
def wikip(title, lang, f):
    """
    Read articles of Wikipedia

    - The default of this command is returns only the summary. Use -f for full.
    - To change the language use -lang and pass a language code.
    """
    wk.set_lang(lang)
    try:
        if f:
            page = wk.page(title)
            article = Text(page.content, justify="left")
            print(Panel(article, title=page.title))
        else:
            summary = Text(wk.summary(title), justify="left")
            print(Panel(summary, title=f"{title} - Summary"))
    except wk.exceptions.DisambiguationError as e:
        print(f"[yellow]Ambiguous title[/yellow]. Options: {', '.join(e.options[:10])}")
    except wk.exceptions.PageError:
        print(f"[red]No article found for '{title}'[/red]")
    except (wk.exceptions.WikipediaException, Exception) as e:
        print(f"[red]Request failed:[/red] {e}")
