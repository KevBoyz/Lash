from rich import print


# ── news ──────────────────────────────────────────────────────────────────────


def impress_news(all_news):
    for news in all_news:
        print(f"\n[link={news['url']}]:magnet:[/link] {news['title']}")
    print("\n")
