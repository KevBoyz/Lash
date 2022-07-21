import click
from pytube import YouTube, Search
import os
import pathlib
from timeit import default_timer
from math import ceil
from tqdm import tqdm


downloads_file = os.path.join(pathlib.Path.home(), 'Downloads')


@click.group('yt', help='Youtube tools')
def yt():
    ...


def on_progress(vid, chunk, bytes_remaining):
    total_size = vid.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage_of_completion = bytes_downloaded / total_size * 100
    totalsz = (total_size / 1024) / 1024
    totalsz = round(totalsz, 1)
    remain = (bytes_remaining / 1024) / 1024
    remain = round(remain, 1)
    dwnd = (bytes_downloaded / 1024) / 1024
    dwnd = round(dwnd, 1)
    percentage_of_completion = round(percentage_of_completion, 2)
    p_bar.reset()
    p_bar.update(int(totalsz - remain))
    p_bar.refresh()


@yt.command(help='download Yt video/audio')
@click.option('-l', type=click.STRING, help='video link')
@click.option('-s', type=click.STRING, help='catch video searching')
@click.option('-a', is_flag=True, help='audio only')
@click.option('-f', type=click.Path(), default=downloads_file, show_default=True, help='output folder')
@click.option('-low', is_flag=True, help='low resolution')
def download(l, s, a, f, low):
    if not s:
        yt = YouTube(l, on_progress_callback=on_progress)
    global p_bar
    print('Getting video', end='')
    if a:
        tic = default_timer()
        video = yt.streams.filter(only_audio=True).first()
        toc = default_timer()
        print(f' - Time Elapsed: {ceil((toc - tic) / 60)}min | (Audio only) Downloading: {video.title}')
        totalsz = int((video.filesize / 1024) / 1024)
        p_bar = tqdm(range(int(totalsz)), colour='green')
        out_file = video.download(output_path=f)
        base, ext = os.path.splitext(out_file)
        new_file = base + '.mp3'
        os.rename(out_file, new_file)
    elif s:
        tic = default_timer()
        search = Search(s)
        video = search.results[0].streams.get_lowest_resolution()
        toc = default_timer()
        print(f' - Time Elapsed: {ceil((toc - tic) / 60)}min | Downloading: {video.title}')
        totalsz = int((video.filesize / 1024) / 1024)
        video.download(f)
    else:
        if low:
            tic = default_timer()
            video = yt.streams.get_lowest_resolution()
            toc = default_timer()
            print(f' - Time Elapsed: {ceil((toc - tic) / 60)}min | Downloading: {video.title}')
            totalsz = int((video.filesize / 1024) / 1024)
            p_bar = tqdm(range(int(totalsz)), colour='green')
            video.download(f)
        else:
            tic = default_timer()
            video = yt.streams.get_highest_resolution()
            toc = default_timer()
            print(f' - Time Elapsed: {ceil((toc - tic) / 60)}min | Downloading: {video.title}')
            total_size = video.filesize
            totalsz = (total_size / 1024) / 1024
            p_bar = tqdm(range(int(totalsz)), colour='green')
            video.download(f)
