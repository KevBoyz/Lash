import os
import pathlib

import click
from rich import print

from lash.plugins.yt.core import download_yt

downloads_folder = os.path.join(pathlib.Path.home(), "Downloads")


@click.command(short_help="Download Youtube video/audio")
@click.option("-l", "link", type=click.STRING, help="Video link")
@click.option("-s", type=click.STRING, help="Video name (for search)")
@click.option("-a", is_flag=True, help="Audio only")
@click.option(
    "-f",
    type=click.Path(),
    default=downloads_folder,
    show_default=True,
    help="output folder",
)
@click.option("-low", is_flag=True, help="Low resolution (video only)")
@click.option(
    "-file",
    type=click.Path(exists=True),
    help="Download multiple videos listed on a text file",
)
def yt(link, s, a, f, low, file):
    """
    This command allows you download videos/audios from Youtube.

    \b
    There are two SIMPLE MANNERS to find your video:
        -l: Paste the video link. This method is more confident.
        -s: Type the video name. The name will be used to search
            for the video. It will use the first result.

    \b
    If you want to AUTOMATE the download process of multiple videos,
    you can create a text file and write the video(s) name(s)/link(s)
    (one for each line). Pass the path of the file using the -file option.

    \b
    For a FAST download you can use -low flag. This will return
    the lowest resolution of the video. The default of this command
    is return the highest resolution.

    \b
    To download only the AUDIO of the video, use the flag -a.
    The download will return a .mp3 file (requires ffmpeg).
    """
    if not file:
        query = link or s
        if not query:
            print("Provide -l (link) or -s (search term)")
            return
        title = download_yt(query, f, low=low, audio_only=a)
        print(f"Download complete: {title}")
    else:
        c = 0
        with open(file, "r") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                c += 1
                print(f"[{c}] Downloading...")
                title = download_yt(line, f, low=low, audio_only=a)
                print(f"[{c}] Done: {title}")
        print(f"All {c} downloads complete")
