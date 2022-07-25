import os
import cv2
import click
import numpy as np
from PIL import Image, ImageDraw
from tqdm import tqdm
from mss import mss
from keyboard import is_pressed
from time import sleep, time
from time import sleep, time
from lash.Exportables.videoTools import *
from math import ceil
from pyautogui import position


@click.group('video', help='Video tolls')
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
    if w:
        for c in range(0, w):
            print(f'{w-c}', end="\r")
            sleep(1)
        print('0', end="\r")
        sleep(1)
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
            print(f'f3 to stop | Recording... {ceil(time()-start)}s | fps {ceil(np.mean(fps))}', end="\r")
            if is_pressed('f3'):
                break
        fps = ceil(np.mean(fps))
        if c:
            conf.close()
    if b:
        pbar = resize_images(False)
        image_folder = os.getcwd()
        video_name = f'{n}.avi'
        os.chdir('..')
        images_list = [img for img in os.listdir(image_folder)
                       if img.endswith(".jpeg")]
        intnumbs = list()
        for file in images_list:
            intnumbs.append(file[:file.find('.')])
            intnumbs.sort(key=int)
        images = list()
        for i in intnumbs:
            images.append(i + '.jpeg')
        if c:
            pbar.reset()
            pbar.set_description('Rendering cursor')
            conf = open(f'{image_folder}/conf.txt', 'r')
            for i, c in enumerate(conf.readlines()):
                try:
                    cord = c[:-1].split()
                    x = int(cord[0])
                    y = int(cord[1])
                    im = Image.open(f'{image_folder}/{images[i]}')
                    draw = ImageDraw.Draw(im)  # Set a Draw object
                    draw.ellipse((x, y, x+20, y+20), fill=(255, 0, 0), outline=(0, 0, 0))
                    im.save(f'{image_folder}/{images[i]}')
                except Exception as e:
                    print(c[:-2].split())
                pbar.update(1)
        if c:
            conf.close()
        pbar.update(pbar.total - pbar.n)
        frame = cv2.imread(os.path.join(image_folder, images[0]))
        height, width, layers = frame.shape
        video = cv2.VideoWriter(video_name, 0, fps, (width, height))
        pbar.reset()
        pbar.set_description('Writing video')
        for image in images:
            video.write(cv2.imread(os.path.join(image_folder, image)))
            pbar.update(1)
        pbar.set_description('Process Compete')
        pbar.update(pbar.total - pbar.n)
        if f:
            pbar.reset()
            pbar.set_description('Clearing folder')
            os.chdir(path)
            for img in os.listdir('.'):
                if img.endswith(".jpeg") or img.endswith(".txt"):
                    os.remove(img)
                pbar.update(1)
        pbar.update(pbar.total - pbar.n)  # Fill 100%
        pbar.close()
        if c:
            ...
        os.chdir('..')
        print(f'Video built and saved in {os.path.join(os.getcwd(), video_name)}')
