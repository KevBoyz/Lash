import os
import re
import subprocess
from PIL import Image


class FfmpegError(RuntimeError):
    """ffmpeg exited with an error; the message is its stderr."""


def get_duration(ffmpeg, path):
    info = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", path], capture_output=True, text=True
    )
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", info.stderr)
    return (
        int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
        if m
        else 0
    )


def run_ffmpeg(cmd, on_progress=None):
    """Run an ffmpeg command that uses `-progress pipe:1`.

    Calls on_progress(seconds_done) on each progress update.
    Raises FfmpegError with ffmpeg's stderr when it fails.
    """
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    for line in proc.stdout:
        if not line.startswith("out_time_ms="):
            continue
        try:
            seconds = int(line.strip().split("=")[1]) / 1_000_000
        except ValueError:
            continue
        if on_progress:
            on_progress(seconds)
    proc.wait()
    if proc.returncode != 0:
        raise FfmpegError(proc.stderr.read())


def get_last(path):
    if path.rfind("\\") != -1:
        last = path[1 + path.rfind("\\"):]
    else:
        last = path[1 + path.rfind("/"):]
    if last.rfind('"'):
        last = last.replace('"', "")
    return last


def get_ext(file="", path=""):
    if path:
        index = path.rfind("\\")
        return path[index + 1:]
    else:
        index = file.rfind(".")
        return file[index:].lower()


def path_no_file(path):
    filename = get_last(path)
    return path.replace(filename, "")


def tuple_to_seconds(times):
    seconds = 0
    seconds += times[0] * 3600
    seconds += times[1] * 60
    seconds += times[2]
    return seconds


def resize_images(r=False):
    path = os.getcwd()
    if r:
        mean_height = 0
        mean_width = 0
        num_of_images = 0
        for file in os.listdir("."):
            if file.endswith((".jpg", ".jpeg", ".png")):
                num_of_images += 1
                im = Image.open(os.path.join(path, file))
                width, height = im.size
                mean_width += width
                mean_height += height
        if num_of_images:
            mean_width = int(mean_width / num_of_images)
            mean_height = int(mean_height / num_of_images)
        for file in os.listdir("."):
            if file.endswith((".jpg", ".jpeg", ".png")):
                im = Image.open(os.path.join(path, file))
                imResize = im.resize((mean_width, mean_height), Image.LANCZOS)
                new_name = file[: file.find(".")] + ".jpeg"
                imResize.save(new_name, "JPEG", quality=95)
                if file != new_name:
                    os.remove(file)
    else:
        for file in os.listdir("."):
            if file.endswith((".jpg", ".png")):
                os.rename(file, file[: file.find(".")] + ".jpeg")
    return [f for f in os.listdir(".") if f.endswith(".jpeg")]
