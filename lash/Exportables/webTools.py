from math import ceil
from pytube import Search
from timeit import default_timer
from rich import print


def get_video_by_link(yt, low=False):
    tic = default_timer()
    if low:
        video = yt.streams.get_lowest_resolution()
    else:
        video = yt.streams.get_highest_resolution()
    toc = default_timer()
    print(f' - Time Elapsed: {ceil((toc - tic) / 60)}min | Downloading: {video.title}', end=' ')
    totalsz = (video.filesize / 1024) / 1024
    return video, totalsz


def get_video_by_search(s, low=False):
    tic = default_timer()
    search = Search(s)
    if low:
        video = search.results[0].streams.get_lowest_resolution()
    else:
        video = search.results[0].streams.get_highest_resolution()
    toc = default_timer()
    print(f' - Time Elapsed: {ceil((toc - tic) / 60)}min | Downloading: {video.title}', end=' ')
    return video


def get_audio_by_link(yt):
    tic = default_timer()
    video = yt.streams.filter(only_audio=True).first()
    toc = default_timer()
    print(f' - Time Elapsed: {ceil((toc - tic) / 60)}min | (Audio only) Downloading: {video.title}', end=' ')
    totalsz = int((video.filesize / 1024) / 1024)
    return video, totalsz


def get_audio_by_search(s):
    tic = default_timer()
    search = Search(s)
    video = search.results[0].streams.filter(only_audio=True).first()
    toc = default_timer()
    print(f' - Time Elapsed: {ceil((toc - tic) / 60)}min | (Audio only) Downloading: {video.title}', end=' ')
    return video


def impress_news(all_news):
    for news in all_news:
        print(f'\n[link={news["url"]}]:magnet:[/link] {news["title"]}')
    print('\n')



