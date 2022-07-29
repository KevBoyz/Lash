import click
from pytube import YouTube, Search
import os
import pathlib
from timeit import default_timer
from math import ceil
from tqdm import tqdm
from lash.Exportables.ytbTools import *


downloads_folder = os.path.join(pathlib.Path.home(), 'Downloads')


@click.group('yt', help='Youtube tools')
def yt():
    ...


def on_progress(vid, chunk, bytes_remaining):
    # bytes_downloaded = total_size - bytes_remaining
    # percentage_of_completion = bytes_downloaded / total_size * 100
    # dwnd = (bytes_downloaded / 1024) / 1024
    # dwnd = round(dwnd, 1)
    # percentage_of_completion = round(percentage_of_completion, 2)
    totalsz = round((vid.filesize / 1024) / 1024, 1)
    remain = round((bytes_remaining / 1024) / 1024, 1)
    p_bar.reset()
    p_bar.update(int(totalsz - remain))
    p_bar.refresh()


@yt.command(help='download Yt video/audio')
@click.option('-l', type=click.STRING, help='video link')
@click.option('-s', type=click.STRING, help='catch video searching')
@click.option('-a', is_flag=True, help='audio only')
@click.option('-f', type=click.Path(), default=downloads_folder, show_default=True, help='output folder')
@click.option('-low', is_flag=True, help='low resolution')
def download(l, s, a, f, low):
    global p_bar
    print('Getting video', end='')
    if l and not a:
        yt = YouTube(l, on_progress_callback=on_progress)
        video, totalsz = get_video_by_link(yt, low)
        p_bar = tqdm(range(int(totalsz)), colour='green')
        video.download(f)
    elif a:
        if l:
            yt = YouTube(l, on_progress_callback=on_progress)
            video, totalsz = get_audio_by_link(yt)
            p_bar = tqdm(range(int(totalsz)), colour='green')
        elif s:
            video = get_audio_by_search(s)
        out_file = video.download(output_path=f)
        base, ext = os.path.splitext(out_file)
        new_file = base + '.mp3'
        os.rename(out_file, new_file)
    elif s and not l:
        video = get_video_by_search(s, low)
        video.download(f)
        print('Download complete')

