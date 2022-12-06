import os
import cv2
from PIL import Image, ImageDraw
from tqdm import tqdm


def resize_images(r=False):
    path = os.path.join(os.getcwd())
    if r:
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
        pbar = tqdm(total=len(os.listdir('.')), colour='green')
        pbar.set_description('Resizing images')
        for file in os.listdir('.'):
            pbar.update(1)
            if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png"):
                im = Image.open(os.path.join(path, file))
                width, height = im.size
                imResize = im.resize((mean_width, mean_height), Image.ANTIALIAS)
                imResize.save(file, 'JPEG', quality=95)
                os.rename(file, file[:file.find('.')] + '.jpeg')
    else:
        pbar = tqdm(total=len(os.listdir('.')), colour='green')
        pbar.set_description('Converting images')
        for file in os.listdir('.'):
            if file.endswith(".jpg") or file.endswith(".png"):
                os.rename(file, file[:file.find('.')] + '.jpeg')
            pbar.update(1)
    pbar.reset()
    return pbar


def alt_build(image_folder, n, c, fps, path, f, images, pbar):
    os.chdir('..')
    video_name = f'{n}.avi'
    frame = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, layers = frame.shape
    video = cv2.VideoWriter(video_name, 0, fps, (width, height))
    pbar.set_description('Writing video')
    pbar.reset()
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


def render_cursor(pbar, image_folder, images):
    pbar.set_description('Rendering cursor')
    pbar.reset()
    conf = open(f'{image_folder}/conf.txt', 'r')
    for i, c in enumerate(conf.readlines()):
        try:
            cord = c[:-1].split()
            x = int(cord[0])
            y = int(cord[1])
            im = Image.open(f'{image_folder}/{images[i]}')
            draw = ImageDraw.Draw(im)  # Set a Draw object
            draw.ellipse((x, y, x + 20, y + 20), fill=(255, 0, 0), outline=(0, 0, 0))
            im.save(f'{image_folder}/{images[i]}')
        except Exception as e:
            pass
        pbar.update(1)
    pbar.update(pbar.total - pbar.n)
    conf.close()


def get_images(image_folder, pbar):
    pbar.set_description('Getting images')
    images_list = [img for img in os.listdir(image_folder)
                   if img.endswith(".jpeg")]
    intnumbs = list()
    for file in images_list:
        intnumbs.append(file[:file.find('.')])
        intnumbs.sort(key=int)
        pbar.update(1)
    pbar.update(pbar.total - pbar.n)
    pbar.reset()
    images = list()
    for i in intnumbs:
        images.append(i + '.jpeg')
        pbar.update(1)
    pbar.update(pbar.total - pbar.n)
    return images


def tuple_to_seconds(times):
    seconds = 0
    seconds += times[0] * 3600
    seconds += times[1] * 60
    seconds += times[2]
    return seconds
