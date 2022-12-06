import click
from moviepy.editor import VideoFileClip, AudioFileClip
from lash.Exportables.fileTools import get_last
from lash.Exportables.videoTools import tuple_to_seconds


@click.group('audio', help='Audio tools')
def audio_group():
    ...


@audio_group.command(help='convert a mp4 video on an mp3 file')
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.option('-o', type=click.STRING, help='output video name, default=original_name')
def get(path, o):
    video = VideoFileClip(path)
    filename = get_last(path)
    if o:
        video.audio.write_audiofile(f'{path.replace(filename, o)}.mp4')
    else:
        video.audio.write_audiofile(path.replace(".mp4", ".mp3"))


@audio_group.command(help='cut a audio')
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.option('-o', type=click.STRING, help='output video name, default=original_name')
@click.option('-i', type=(int, int, int), help='initial time for cut. Put in format (hh mm ss)')
@click.option('-f', type=(int, int, int), help='final time for cut. Put in format (hh mm ss)')
def cut(path, o, i, f):
    audio = AudioFileClip(path)
    filename = get_last(path)
    initial_time = tuple_to_seconds(i)
    final_time = tuple_to_seconds(f)
    clip = audio.subclip(initial_time, final_time)
    try:
        if o:
            clip.write_audiofile(f'{path.replace(filename, o)}.mp3')
        else:
            clip.write_audiofile(path)
    except OSError:
        pass
