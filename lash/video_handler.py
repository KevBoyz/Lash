import click
import os
import cv2
from PIL import Image
from tqdm import tqdm
from mss import mss
from lash.Exportables.videoTools import *
from time import sleep, time
import numpy as np


@click.group('video', help='Video tolls')
def video():
    ...


@video.command(help='Build a video with multiple images')
@click.argument('path', metavar='<path>', type=click.Path(exists=True), required=False, default='.')
@click.option('-fps', type=click.INT, help='Fps', default=5, show_default=True)
@click.option('-n', type=click.STRING, help='Video name', default='video', show_default=True)
@click.option('-num', is_flag=True, help='Numeric sequence of images', default=True, show_default=True)
@click.option('-r', is_flag=True, help='Resize all images before build', default=False, show_default=True)
def build(path, fps, n, num, r):
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
    pbar.close()
    print(f'Video built and saved in {os.path.join(os.getcwd(), video_name)}')


@video.command(help='Rec your monitor')
@click.argument('path', metavar='<path>', type=click.Path(exists=True), required=False, default='.')
@click.option('-t', type=click.INT, help='Time limit in seconds')
@click.option('-w', type=click.INT, help='Wait some seconds before start')
@click.option('-c', is_flag=True, default=False, show_default=True, help='Capture cursor (fps reduction)')
@click.option('-b', is_flag=True, default=False, show_default=True, help='Build video after record')
@click.option('-f', is_flag=True, default=False, show_default=True, help='Delete frames after build')
def rec(path, t, w, c, b, f):
    os.chdir(path)
    if w:
        for c in range(0, w):
            print(f'{w-c}', end="\r")
            sleep(1)
        print(0)
    fps = list()
    with mss() as mss_instance:
        for c in range(0, 10000):
            last_time = time()
            mss_instance.shot(output=f'{c}.jpeg')
            fps.append(1 / (time() - last_time))
            print(np.mean(fps))

