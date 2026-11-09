import os
import tempfile
from math import trunc
from pathlib import Path

import click
import cv2
import imageio_ffmpeg
from moviepy import VideoFileClip, concatenate_videoclips
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn

from lash.plugins.video.core import (
    FfmpegError,
    get_duration,
    get_ext,
    get_last,
    resize_images,
    run_ffmpeg,
    tuple_to_seconds,
)

console = Console()


@click.group("video", help="Build, cut, and compose videos")
def video(): ...


@video.command()
@click.argument(
    "path",
    metavar="<path>",
    type=click.Path(exists=True),
    required=False,
    default=".",
)
@click.option(
    "-fps",
    type=click.INT,
    help="Frames per second",
    default=5,
    show_default=True,
)
@click.option("-n", type=click.STRING, help="Output video name (no extension)")
@click.option(
    "-num",
    is_flag=True,
    help="Sort images numerically (1.jpeg, 2.jpeg, ...)",
    default=True,
    show_default=True,
)
@click.option(
    "-r",
    is_flag=True,
    help="Resize all images to match the first before building",
    default=False,
    show_default=True,
)
def build(path, fps, n, num, r):
    """Build a video from a folder of images.

    \b
    Images in the target folder must be JPEG files.
    With -num (default), sorted numerically by filename (1.jpeg, 2.jpeg, ...).
    Without -num, sorted alphabetically.
    Output is saved as an AVI file in the parent folder.

    \b
    Example:
      lash video build ./frames
      lash video build ./frames -fps 24 -n recording
    """
    if not n:
        n = "video"
    os.chdir(path)
    image_folder = os.getcwd()
    video_name = f"{n}.avi"
    os.chdir("..")

    images = resize_images(r)
    if num:
        nums = sorted([f[: f.find(".")] for f in images], key=int)
        images = [i + ".jpeg" for i in nums]
    else:
        images.sort()

    frame = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, layers = frame.shape
    video_writer = cv2.VideoWriter(video_name, 0, fps, (width, height))

    with Progress(
        TextColumn("[bold cyan]Writing video"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("", total=len(images))
        for image in images:
            video_writer.write(cv2.imread(os.path.join(image_folder, image)))
            progress.advance(task)

    jpegs = [img for img in os.listdir(".") if img.endswith(".jpeg")]
    with Progress(
        TextColumn("[bold cyan]Clearing folder"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("", total=len(jpegs))
        for img in jpegs:
            os.remove(img)
            progress.advance(task)

    console.print(
        f"[green]Saved:[/green] {os.path.join(os.getcwd(), video_name)}"
    )


@video.command(help="Create a 13-second highlight reel from a video")
@click.argument("path", metavar="<path>", type=click.Path(exists=True))
def resume(path):
    file_name = get_last(path)
    ext = get_ext(file_name)
    new_name = file_name.replace(" ", "_").replace(ext, "") + "-resume" + ext
    new_path = path.replace(file_name, new_name)
    clip = VideoFileClip(path).without_audio()
    interval = trunc(clip.duration / 13)
    resume_time = 0
    concat_list = []
    for _ in range(12):
        concat_list.append(clip.subclipped(resume_time, resume_time + 1.3))
        resume_time += interval
    resume_clip = concatenate_videoclips(concat_list, method="compose")
    with console.status("[cyan]Rendering resume..."):
        resume_clip.write_videofile(new_path, logger=None)


@video.command(help="Prepend an intro clip to a video")
@click.argument("video_path",
                metavar="<video_path>",
                type=click.Path(exists=True))
@click.argument("video_intro",
                metavar="<video_into>",
                type=click.Path(exists=True))
@click.option("-s", is_flag=True, help="overwrite original file")
def intro(video_path, video_intro, s):
    p = Path(video_path)
    out = video_path if s else str(p.with_stem(p.stem + "_with_intro"))
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    total = get_duration(ffmpeg, video_intro) + get_duration(ffmpeg, video_path)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(f"file '{video_intro}'\nfile '{video_path}'\n")
        list_file = f.name

    try:
        cmd = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            list_file,
            "-c",
            "copy",
            "-progress",
            "pipe:1",
            out,
        ]
        with Progress(
            TextColumn("[bold cyan]Adding intro"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("", total=total)
            run_ffmpeg(cmd, lambda done: progress.update(task, completed=min(done, total)))
    except FfmpegError as e:
        raise click.ClickException(str(e)) from None
    finally:
        os.unlink(list_file)


@video.command(help="Append an end clip to a video")
@click.argument("video_path",
                metavar="<video_path>",
                type=click.Path(exists=True))
@click.argument("video_end", metavar="<video_end>",
                type=click.Path(exists=True))
@click.option("-s", is_flag=True, help="overwrite original file")
def end(video_path, video_end, s):
    p = Path(video_path)
    out = video_path if s else str(p.with_stem(p.stem + "_with_end"))
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    total = get_duration(ffmpeg, video_path) + get_duration(ffmpeg, video_end)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(f"file '{video_path}'\nfile '{video_end}'\n")
        list_file = f.name

    try:
        cmd = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            list_file,
            "-c",
            "copy",
            "-progress",
            "pipe:1",
            out,
        ]
        with Progress(
            TextColumn("[bold cyan]Adding end"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("", total=total)
            run_ffmpeg(cmd, lambda done: progress.update(task, completed=min(done, total)))
    except FfmpegError as e:
        raise click.ClickException(str(e)) from None
    finally:
        os.unlink(list_file)


@video.command()
@click.argument("path", metavar="<path>", type=click.Path(exists=True))
@click.option("-s", is_flag=True, help="Overwrite the original file")
@click.option("-i", type=(int, int, int),
              help="Start time as h m s (e.g. -i 0 1 30)")
@click.option("-f", type=(int, int, int),
              help="End time as h m s (e.g. -f 0 3 0)")
def cut(path, s, i, f):
    """Cut a segment from a video.

    \b
    Output is saved as <name>_cutted.<ext> by default.
    Use -s to overwrite the original file.
    Omitting -i starts from the beginning; omitting -f goes to the end.

    \b
    Example:
      lash video cut clip.mp4 -i 0 0 30 -f 0 2 0
      lash video cut clip.mp4 -s -f 0 1 0
    """
    p = Path(path)
    out = path if s else str(p.with_stem(p.stem + "_cutted"))
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    total = get_duration(ffmpeg, path)
    start_t = tuple_to_seconds(i) if i else 0
    end_t = tuple_to_seconds(f) if f else total
    cut_duration = end_t - start_t

    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", path]
    if i:
        cmd += ["-ss", str(start_t)]
    if f:
        cmd += ["-to", str(end_t)]
    cmd += ["-c", "copy", "-progress", "pipe:1", out]
    with Progress(
        TextColumn("[bold cyan]Cutting"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("", total=cut_duration)
        try:
            run_ffmpeg(cmd, lambda done: progress.update(task, completed=min(done, cut_duration)))
        except FfmpegError as e:
            raise click.ClickException(str(e)) from None
