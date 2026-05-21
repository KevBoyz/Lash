import re
import subprocess
from pathlib import Path

import click
import imageio_ffmpeg
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn

from lash.plugins.audio.core import tuple_to_seconds


@click.group('audio', help='Audio tools')
def audio_group():
    ...


@audio_group.command(help='Extract audio from a video file and save as MP3')
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.option('-o', type=click.STRING, help='output file name without extension')
def get(path, o):
    p = Path(path)
    out = str(p.with_name(o + '.mp3') if o else p.with_suffix('.mp3'))
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    info = subprocess.run([ffmpeg, '-hide_banner', '-i', path], capture_output=True, text=True)
    match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', info.stderr)
    total = int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3)) if match else 0

    cmd = [ffmpeg, '-y', '-hide_banner', '-loglevel', 'error', '-i', path,
           '-vn', '-q:a', '0', '-progress', 'pipe:1', out]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    with Progress(
        TextColumn("[bold cyan]Extracting"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("", total=total)
        for line in proc.stdout:
            if line.startswith('out_time_ms='):
                try:
                    ms = int(line.strip().split('=')[1])
                    progress.update(task, completed=min(ms / 1_000_000, total))
                except ValueError:
                    pass

    proc.wait()
    if proc.returncode != 0:
        raise click.ClickException(proc.stderr.read())


@audio_group.command(help='Cut a segment from an audio file')
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.option('-s', is_flag=True, help='Overwrite the original file')
@click.option('-i', type=(int, int, int), help='Start time as h m s (e.g. -i 0 1 30)')
@click.option('-f', type=(int, int, int), help='End time as h m s (e.g. -f 0 3 0)')
def cut(path, s, i, f):
    p = Path(path)
    out = path if s else str(p.with_stem(p.stem + '_cutted'))
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    info = subprocess.run([ffmpeg, '-hide_banner', '-i', path], capture_output=True, text=True)
    match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', info.stderr)
    total = int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3)) if match else 0
    start_t = tuple_to_seconds(i) if i else 0
    end_t = tuple_to_seconds(f) if f else total
    cut_duration = end_t - start_t

    cmd = [ffmpeg, '-y', '-hide_banner', '-loglevel', 'error', '-i', path]
    if i:
        cmd += ['-ss', str(start_t)]
    if f:
        cmd += ['-to', str(end_t)]
    cmd += ['-c', 'copy', '-progress', 'pipe:1', out]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    with Progress(
        TextColumn("[bold cyan]Cutting"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("", total=cut_duration)
        for line in proc.stdout:
            if line.startswith('out_time_ms='):
                try:
                    ms = int(line.strip().split('=')[1])
                    progress.update(task, completed=min(ms / 1_000_000, cut_duration))
                except ValueError:
                    pass

    proc.wait()
    if proc.returncode != 0:
        raise click.ClickException(proc.stderr.read())
