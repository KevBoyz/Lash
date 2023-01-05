import os
from cv2 import imread, VideoWriter  # The IDE can show an error, but all is working
import click
from numpy import mean
from mss import mss
from tqdm import tqdm
from math import ceil, trunc
from time import sleep, time
from pyautogui import position
from keyboard import is_pressed
from moviepy.editor import VideoFileClip, concatenate_videoclips
from lash.Exportables.videoTools import *
from lash.Exportables.fileTools import get_last, get_ext, path_no_file


@click.group('video', help='Video tools')
def video():
    ...


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
    pbar = resize_images(r)
    image_folder = os.getcwd()
    video_name = f'{n}.avi'
    os.chdir('..')
    images_list = [img for img in os.listdir(image_folder)
                   if img.endswith(".jpeg")]
    if num:
        intnumbs = list()
        for file in images_list:
            intnumbs.append(file[:file.find('.')])
            intnumbs.sort(key=int)
        images = list()
        for i in intnumbs:
            images.append(i + '.jpeg')
    else:
        images_list.sort()
        images = images_list
    frame = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, layers = frame.shape
    video = cv2.VideoWriter(video_name, 0, fps, (width, height))
    pbar.set_description('Writing video')
    for image in images:
        video.write(cv2.imread(os.path.join(image_folder, image)))
        pbar.update(1)
    pbar.set_description('Process Compete')
    pbar.update(pbar.total - pbar.n)  # Fill 100%
    pbar.reset()
    pbar.set_description('Clearing folder')
    for img in os.listdir('.'):
        if img.endswith(".jpeg"):
            os.remove(img)
            pbar.update(1)
    pbar.close()
    print(f'Video built and saved in {os.path.join(os.getcwd(), video_name)}')



@video.command(help='Rec your monitor')
@click.argument('path', metavar='<path>', type=click.Path(exists=True), required=False, default='.')
@click.option('-w', type=click.INT, help='Wait some seconds before start')
@click.option('-n', type=click.STRING, default='video', show_default=True, help='Video name')
@click.option('-c', is_flag=True, default=True, show_default=True, help='Capture cursor (fps reduction)')
@click.option('-b', is_flag=True, default=True, show_default=True, help='Build video after record')
@click.option('-f', is_flag=True, default=True, show_default=True, help='Delete frames after build')
def rec(path, w, n, c, b, f):
    os.chdir(path)
    image_folder = os.getcwd()
    if w:
        for c in range(0, w):
            print(f'{w-c}', end="\r")
            sleep(1)
        print('0', end="\r")
    fps = list()
    if c:
        conf = open('conf.txt', 'w')
    with mss() as mss_instance:
        s = 0
        start = time()
        while True:
            s += 1
            last_time = time()
            mss_instance.shot(output=f'{s}.jpeg')
            fps.append(1 / (time() - last_time))
            if c:
                posx = str(position().x)
                posy = str(position().y)
                conf.write(f'{posx} {posy}\n')
            print(f'f3 to stop | Recording... {ceil(time()-start)}s | fps {ceil(mean(fps))}', end="\r")
            if is_pressed('f3'):
                break
        fps = ceil(mean(fps))
        if c:
            conf.close()
    pbar = tqdm(total=len(os.listdir('.')), colour='green')
    images = get_images(image_folder, pbar)
    if c:
        render_cursor(pbar, image_folder, images)
    if b:
        alt_build(n=n, c=c, fps=fps, path=path, f=f, image_folder=image_folder, pbar=pbar, images=images)
    else:
        print(f'Process complete. Build with $ lash video build {path}')


@video.command(help='Resume a video')
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
def resume(path):
    file_name = get_last(path)
    ext = get_ext(file_name)
    new_name = file_name.replace(' ', '_').replace(ext, '') + '-resume' + ext
    new_path = path.replace(file_name, new_name)
    video = VideoFileClip(path).without_audio()
    interval = trunc(video.duration / 13)
    resume_time = 0
    concat_list = list()
    for c in range(0, 12):
        sub = video.subclip(resume_time, resume_time+1.3)
        concat_list.append(sub)
        resume_time += interval
    resume_video = concatenate_videoclips(concat_list, method='compose')
    resume_video.write_videofile(new_path)


@video.command(help='Add a intro to one video')
@click.argument('video_path', metavar='<video_path>', type=click.Path(exists=True))
@click.argument('video_intro', metavar='<video_into>', type=click.Path(exists=True))
@click.option('-o', type=click.STRING, help='output video name, default=original_name')
def intro(video_path, video_intro, o):
    video = VideoFileClip(video_path)
    intro = VideoFileClip(video_intro)
    composed = concatenate_videoclips([intro, video])
    filename = get_last(video_path)
    if o:
        composed.write_videofile(f'{video_path.replace(filename, o)}.mp4')
    else:
        composed.write_videofile(video_path)


@video.command(help='Add a end to one video')
@click.argument('video_path', metavar='<video_path>', type=click.Path(exists=True))
@click.argument('video_end', metavar='<video_end>', type=click.Path(exists=True))
@click.option('-o', type=click.STRING, help='output video name, default=original_name')
def end(video_path, video_end, o):
    video = VideoFileClip(video_path)
    end = VideoFileClip(video_end)
    composed = concatenate_videoclips([video, end])
    filename = get_last(video_path)
    if o:
        composed.write_videofile(f'{video_path.replace(filename, o)}.mp4')
    else:
        composed.write_videofile(video_path)


@video.command(help='cut a video')
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.option('-o', type=click.STRING, help='output video name, default=original_name')
@click.option('-i', type=(int, int, int), help='initial time for cut. Put in format (hh mm ss)')
@click.option('-f', type=(int, int, int), help='final time for cut. Put in format (hh mm ss)')
def cut(path, o, i, f):
    video = VideoFileClip(path)
    filename = get_last(path)
    initial_time = tuple_to_seconds(i)
    final_time = tuple_to_seconds(f)
    clip = video.subclip(initial_time, final_time)
    try:
        if o:
            clip.write_videofile(f'{path.replace(filename, o)}.mp4')
        else:
            clip.write_videofile(path)
    except OSError:
        pass

