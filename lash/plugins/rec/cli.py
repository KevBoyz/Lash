import os
from math import ceil
from time import sleep, time

import click
from numpy import mean
from rich.console import Console

from lash.plugins.rec.core import alt_build, get_images, render_cursor

console = Console()


@click.command()
@click.argument(
    "path",
    metavar="<path>",
    type=click.Path(exists=True),
    required=False,
    default=".",
)
@click.option(
    "-w",
    type=click.INT,
    help="Countdown in seconds before recording starts",
)
@click.option(
    "-n",
    type=click.STRING,
    default="video",
    show_default=True,
    help="Output video name",
)
@click.option(
    "-c",
    is_flag=True,
    default=True,
    show_default=True,
    help="Overlay cursor on frames (slight fps cost)",
)
@click.option(
    "-b",
    is_flag=True,
    default=True,
    show_default=True,
    help="Build video automatically after recording",
)
@click.option(
    "-f",
    is_flag=True,
    default=True,
    show_default=True,
    help="Delete frames after building the video",
)
def rec(path, w, n, c, b, f):
    """Record your monitor screen (F3 to stop).

    \b
    Captures frames at maximum speed and assembles them into an AVI.
    Cursor overlay is included by default; disable with --no-c.
    Video is built automatically after stopping; disable with --no-b.

    \b
    Example:
      lash rec
      lash rec -w 3 -n my_recording ./output_folder
    """
    from keyboard import is_pressed
    from mss import mss
    from pyautogui import position

    os.chdir(path)
    image_folder = os.getcwd()

    if w:
        for countdown in range(w, 0, -1):
            console.print(f"{countdown}", end="\r")
            sleep(1)
        console.print("0", end="\r")

    fps_list = []
    if c:
        conf = open("conf.txt", "w")

    with mss() as mss_instance:
        s = 0
        start = time()
        while True:
            s += 1
            last_time = time()
            mss_instance.shot(output=f"{s}.jpeg")
            fps_list.append(1 / (time() - last_time))
            if c:
                conf.write(f"{position().x} {position().y}\n")
            console.print(
                f"[bold]f3 to stop[/bold] | Recording... "
                f"{ceil(time() - start)}s | fps {ceil(mean(fps_list))}",
                end="\r",
            )
            if is_pressed("f3"):
                break
        fps_avg = ceil(mean(fps_list))
        if c:
            conf.close()

    with console.status("[cyan]Processing frames..."):
        images = get_images(image_folder)
        if c:
            render_cursor(image_folder, images)

    if b:
        with console.status("[cyan]Building video..."):
            video_path = alt_build(
                n=n,
                fps=fps_avg,
                path=path,
                f=f,
                image_folder=image_folder,
                images=images,
            )
        console.print(f"[green]Saved:[/green] {video_path}")
    else:
        console.print("Process complete. Build with: lash video build <path>")
