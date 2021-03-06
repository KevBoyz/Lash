import click
import os
import cv2
from PIL import Image
from tqdm import tqdm
from lash.Exportables.videoTools import *


@click.group('video', help='Video tolls')
def video():
    ...


@video.command(help='Build a video with multiple images')
@click.argument('path', metavar='<path>', type=click.Path(exists=True), required=False, default='.')
@click.option('-fps', type=click.INT, help='Fps', default=5, show_default=True)
@click.option('-n', type=click.STRING, help='Video name', default='video', show_default=True)
def build(path, fps, n):
    os.chdir(path)
    pbar = resize_images()
    image_folder = os.getcwd()
    video_name = f'{n}.avi'
    os.chdir('..')
    images_list = [img for img in os.listdir(image_folder)
                   if img.endswith(".jpg") or
                   img.endswith(".jpeg") or
                   img.endswith(".png")]
    images_list.sort()
    images = convert_to_png(images_list)
    frame = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, layers = frame.shape
    video = cv2.VideoWriter(video_name, 0, fps, (width, height))
    for image in images:
        pbar.set_description('Writing video')
        pbar.update(1)
        video.write(cv2.imread(os.path.join(image_folder, image)))
    pbar.set_description('Process Compete')
    pbar.update(pbar.total - pbar.n)  # Fill 100%
    pbar.close()
    print(f'Video built and saved in {os.path.join(os.getcwd(), video_name)}')

