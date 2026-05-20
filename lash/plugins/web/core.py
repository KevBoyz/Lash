import yt_dlp
from rich import print


def download_yt(url_or_query, output_path, low=False, audio_only=False):
    is_search = not url_or_query.startswith(('http://', 'https://'))
    url = f'ytsearch1:{url_or_query}' if is_search else url_or_query

    if audio_only:
        fmt = 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio'
    elif low:
        fmt = 'worst[ext=mp4]/worst'
    else:
        fmt = 'best[ext=mp4]/best'

    ydl_opts = {
        'format': fmt,
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if 'entries' in info:
            info = info['entries'][0]

    return info.get('title', 'Unknown')


def impress_news(all_news):
    for news in all_news:
        print(f'\n[link={news["url"]}]:magnet:[/link] {news["title"]}')
    print('\n')
