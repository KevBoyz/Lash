def format_news(all_news):
    """Rich markup listing each news item as a clickable title."""
    items = "".join(
        f"\n[link={news['url']}]:magnet:[/link] {news['title']}\n" for news in all_news
    )
    return items + "\n"
