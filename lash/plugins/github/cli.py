import click
import bs4
import requests as r
from rich import print
from rich.console import Console
from rich.table import Table


@click.command(short_help="Scrape a Github profile")
@click.argument("nick", type=click.STRING)
@click.option("-op", is_flag=True, help="Open the user page on browser")
def github(nick, op):
    """
    \b
    This command going to scrape github.com/NICK and take:
    Activity, followers, repositories and bio.
    """
    try:
        api_resp = r.get(
            f"https://api.github.com/users/{nick}",
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        if api_resp.status_code != 200:
            print("Error, profile not found")
            return
        data = api_resp.json()

        contrib_resp = r.get(
            f"https://github.com/users/{nick}/contributions",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        contrib_soup = bs4.BeautifulSoup(contrib_resp.text, "html.parser")

        contrib_h2 = contrib_soup.find("h2", "f4 text-normal mb-2")
        contributions = contrib_h2.text.split()[0] if contrib_h2 else "N/A"

        days = contrib_soup.find_all("td", "ContributionCalendar-day")
        recent = days[-7:] if len(days) >= 7 else days

        bio = data.get("bio") or ""
        if len(bio) > 60:
            bio = bio[:60] + "..."

        url = f"https://github.com/{nick}"
        print(
            f"\nUsrInf :: [bold green]{data['login']}[/bold green]"
            f" -> {contributions} contributions,"
            f" {data['followers']} followers, {data['public_repos']} repos\n"
            f"UsrBio :: [italic]{bio}[/italic]\n"
        )
        table = Table(title="User activity")
        table.add_column("Date", style="cyan", justify="center")
        table.add_column("Level", style="green", justify="left")
        for day in recent:
            date = day.get("data-date", "")
            level = day.get("data-level", "0")
            table.add_row(date, ("■ " * int(level)).strip())
        Console().print(table)
        if op:
            click.launch(url)
    except Exception as e:
        print(e)
