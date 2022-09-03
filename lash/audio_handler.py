import os

import click
from moviepy.editor import VideoFileClip, AudioClip
from lash.Exportables.fileTools import path_no_file, get_last


@click.group('audio', help='Audio tools')
def audio():
    ...


@audio.command(help='convert a mp4 video on an mp3 file')
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.option('-o', type=click.STRING, help='output video name, default=original_name')
def get(path, o):
    video = VideoFileClip(path)
    filename = get_last(path)
    if o:
        video.audio.write_audiofile(f'{path.replace(filename, o)}.mp4')
    else:
        video.audio.write_audiofile(path.replace(".mp4", ".mp3"))
