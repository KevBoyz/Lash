import click
from moviepy.editor import VideoFileClip, AudioClip
from lash.Exportables.fileTools import get_file


@click.group('audio', help='Audio tools')
def audio():
    ...


@audio.command(help='convert a mp4 video on an mp3 file')
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
def get(path):
    video = VideoFileClip(path)
    video.audio.write_audiofile(f'{path.replace(".mp4", ".mp3")}')
