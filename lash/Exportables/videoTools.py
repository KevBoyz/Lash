import os
import cv2
from PIL import Image
from tqdm import tqdm


def resize_images():
    path = os.path.join(os.getcwd())
    mean_height = 0
    mean_width = 0
    num_of_images = 0
    for file in os.listdir('.'):
        if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png"):
            num_of_images += 1
            im = Image.open(os.path.join(path, file))
            width, height = im.size
            mean_width += width
            mean_height += height
    mean_width = int(mean_width / num_of_images)
    mean_height = int(mean_height / num_of_images)
    pbar = tqdm(total=len(os.listdir('.') * 2), colour='green')
    pbar.set_description('Resizing images')
    for file in os.listdir('.'):
        pbar.update(1)
        if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png"):
            im = Image.open(os.path.join(path, file))
            width, height = im.size
            imResize = im.resize((mean_width, mean_height), Image.ANTIALIAS)
            imResize.save(file, 'JPEG', quality=95)
    return pbar


def convert_to_png(images_list):
    images = list()
    for i in images_list:
        if i[i.find('.'):] != '.png':
            images.append(i.replace(i[i.find('.'):], '.png'))
        else:
            images.append(i)
    return images
