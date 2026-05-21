import os
import re
import subprocess
import tempfile
from math import ceil, trunc
from pathlib import Path
from time import sleep, time

import click
import cv2
import imageio_ffmpeg
from moviepy import VideoFileClip, concatenate_videoclips
from numpy import mean
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn

from lash.plugins.video.core import (
    alt_build, get_ext, get_images, get_last,
    render_cursor, resize_images, tuple_to_seconds,
)

console = Console()


@click.group('video', help='Video tools')
def video():
    ...


def _get_duration(ffmpeg, path):
    info = subprocess.run([ffmpeg, '-hide_banner', '-i', path], capture_output=True, text=True)
    m = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', info.stderr)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0


def _run_ffmpeg(cmd, label, total):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    with Progress(
        TextColumn(f'[bold cyan]{label}'),
        BarColumn(),
        '[progress.percentage]{task.percentage:>3.0f}%',
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task('', total=total)
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


@video.command(help='Build a video with multiple images')
@click.argument('path', metavar='<path>', type=click.Path(exists=True), required=False, default='.')
@click.option('-fps', type=click.INT, help='Fps', default=5, show_default=True)
@click.option('-n', type=click.STRING, help='Video name')
@click.option('-num', is_flag=True, help='Numeric sequence of images', default=True, show_default=True)
@click.option('-r', is_flag=True, help='Resize all images before build', default=False, show_default=True)
def build(path, fps, n, num, r):
    if not n:
        n = 'video'
    os.chdir(path)
    image_folder = os.getcwd()
    video_name = f'{n}.avi'
    os.chdir('..')

    images = resize_images(r)
    if num:
        nums = sorted([f[:f.find('.')] for f in images], key=int)
        images = [i + '.jpeg' for i in nums]
    else:
        images.sort()

    frame = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, layers = frame.shape
    video_writer = cv2.VideoWriter(video_name, 0, fps, (width, height))

    with Progress(
        TextColumn('[bold cyan]Writing video'),
        BarColumn(),
        '[progress.percentage]{task.percentage:>3.0f}%',
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task('', total=len(images))
        for image in images:
            video_writer.write(cv2.imread(os.path.join(image_folder, image)))
            progress.advance(task)

    jpegs = [img for img in os.listdir('.') if img.endswith('.jpeg')]
    with Progress(
        TextColumn('[bold cyan]Clearing folder'),
        BarColumn(),
        '[progress.percentage]{task.percentage:>3.0f}%',
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task('', total=len(jpegs))
        for img in jpegs:
            os.remove(img)
            progress.advance(task)

    console.print(f'[green]Saved:[/green] {os.path.join(os.getcwd(), video_name)}')


@video.command(help='Record your monitor screen (F3 to stop)')
@click.argument('path', metavar='<path>', type=click.Path(exists=True), required=False, default='.')
@click.option('-w', type=click.INT, help='Wait some seconds before start')
@click.option('-n', type=click.STRING, default='video', show_default=True, help='Video name')
@click.option('-c', is_flag=True, default=True, show_default=True, help='Capture cursor (fps reduction)')
@click.option('-b', is_flag=True, default=True, show_default=True, help='Build video after record')
@click.option('-f', is_flag=True, default=True, show_default=True, help='Delete frames after build')
def rec(path, w, n, c, b, f):
    from keyboard import is_pressed
    from mss import mss
    from pyautogui import position

    os.chdir(path)
    image_folder = os.getcwd()

    if w:
        for countdown in range(w, 0, -1):
            console.print(f'{countdown}', end='\r')
            sleep(1)
        console.print('0', end='\r')

    fps_list = []
    if c:
        conf = open('conf.txt', 'w')

    with mss() as mss_instance:
        s = 0
        start = time()
        while True:
            s += 1
            last_time = time()
            mss_instance.shot(output=f'{s}.jpeg')
            fps_list.append(1 / (time() - last_time))
            if c:
                conf.write(f'{position().x} {position().y}\n')
            console.print(
                f'[bold]f3 to stop[/bold] | Recording... {ceil(time()-start)}s | fps {ceil(mean(fps_list))}',
                end='\r',
            )
            if is_pressed('f3'):
                break
        fps_avg = ceil(mean(fps_list))
        if c:
            conf.close()

    with console.status('[cyan]Processing frames...'):
        images = get_images(image_folder)
        if c:
            render_cursor(image_folder, images)

    if b:
        with console.status('[cyan]Building video...'):
            video_path = alt_build(n=n, fps=fps_avg, path=path, f=f, image_folder=image_folder, images=images)
        console.print(f'[green]Saved:[/green] {video_path}')
    else:
        console.print(f'Process complete. Build with: lash video build {path}')


@video.command(help='Create a 13-second highlight reel from a video')
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
def resume(path):
    file_name = get_last(path)
    ext = get_ext(file_name)
    new_name = file_name.replace(' ', '_').replace(ext, '') + '-resume' + ext
    new_path = path.replace(file_name, new_name)
    clip = VideoFileClip(path).without_audio()
    interval = trunc(clip.duration / 13)
    resume_time = 0
    concat_list = []
    for _ in range(12):
        concat_list.append(clip.subclipped(resume_time, resume_time + 1.3))
        resume_time += interval
    resume_clip = concatenate_videoclips(concat_list, method='compose')
    with console.status('[cyan]Rendering resume...'):
        resume_clip.write_videofile(new_path, logger=None)


@video.command(help='Prepend an intro clip to a video')
@click.argument('video_path', metavar='<video_path>', type=click.Path(exists=True))
@click.argument('video_intro', metavar='<video_into>', type=click.Path(exists=True))
@click.option('-s', is_flag=True, help='overwrite original file')
def intro(video_path, video_intro, s):
    p = Path(video_path)
    out = video_path if s else str(p.with_stem(p.stem + '_with_intro'))
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    total = _get_duration(ffmpeg, video_intro) + _get_duration(ffmpeg, video_path)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(f"file '{video_intro}'\nfile '{video_path}'\n")
        list_file = f.name

    try:
        cmd = [ffmpeg, '-y', '-hide_banner', '-loglevel', 'error',
               '-f', 'concat', '-safe', '0', '-i', list_file,
               '-c', 'copy', '-progress', 'pipe:1', out]
        _run_ffmpeg(cmd, 'Adding intro', total)
    finally:
        os.unlink(list_file)


@video.command(help='Append an end clip to a video')
@click.argument('video_path', metavar='<video_path>', type=click.Path(exists=True))
@click.argument('video_end', metavar='<video_end>', type=click.Path(exists=True))
@click.option('-s', is_flag=True, help='overwrite original file')
def end(video_path, video_end, s):
    p = Path(video_path)
    out = video_path if s else str(p.with_stem(p.stem + '_with_end'))
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    total = _get_duration(ffmpeg, video_path) + _get_duration(ffmpeg, video_end)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(f"file '{video_path}'\nfile '{video_end}'\n")
        list_file = f.name

    try:
        cmd = [ffmpeg, '-y', '-hide_banner', '-loglevel', 'error',
               '-f', 'concat', '-safe', '0', '-i', list_file,
               '-c', 'copy', '-progress', 'pipe:1', out]
        _run_ffmpeg(cmd, 'Adding end', total)
    finally:
        os.unlink(list_file)


@video.command(help='Cut a segment from a video')
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.option('-s', is_flag=True, help='overwrite original file')
@click.option('-i', type=(int, int, int), help='initial time for cut. Put in format (hh mm ss)')
@click.option('-f', type=(int, int, int), help='final time for cut. Put in format (hh mm ss)')
def cut(path, s, i, f):
    p = Path(path)
    out = path if s else str(p.with_stem(p.stem + '_cutted'))
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    info = subprocess.run([ffmpeg, '-hide_banner', '-i', path], capture_output=True, text=True)
    m = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', info.stderr)
    total = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0
    start_t = tuple_to_seconds(i) if i else 0
    end_t = tuple_to_seconds(f) if f else total
    cut_duration = end_t - start_t

    cmd = [ffmpeg, '-y', '-hide_banner', '-loglevel', 'error', '-i', path]
    if i:
        cmd += ['-ss', str(start_t)]
    if f:
        cmd += ['-to', str(end_t)]
    cmd += ['-c', 'copy', '-progress', 'pipe:1', out]
    _run_ffmpeg(cmd, 'Cutting', cut_duration)
