import os
import cv2
from PIL import Image, ImageDraw


def alt_build(image_folder, n, fps, path, f, images):
    os.chdir("..")
    video_name = f"{n}.avi"
    frame = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, layers = frame.shape
    video = cv2.VideoWriter(video_name, 0, fps, (width, height))
    for image in images:
        video.write(cv2.imread(os.path.join(image_folder, image)))
    if f:
        os.chdir(path)
        for img in os.listdir("."):
            if img.endswith(".jpeg") or img.endswith(".txt"):
                os.remove(img)
    os.chdir("..")
    return os.path.join(os.getcwd(), video_name)


def render_cursor(image_folder, images):
    conf = open(f"{image_folder}/conf.txt", "r")
    for i, c in enumerate(conf.readlines()):
        try:
            cord = c[:-1].split()
            x = int(cord[0])
            y = int(cord[1])
            im = Image.open(f"{image_folder}/{images[i]}")
            draw = ImageDraw.Draw(im)
            draw.ellipse((x, y, x + 20, y + 20),
                         fill=(255, 0, 0), outline=(0, 0, 0))
            im.save(f"{image_folder}/{images[i]}")
        except Exception:
            pass
    conf.close()


def get_images(image_folder):
    images_list = [img for img in os.listdir(
        image_folder) if img.endswith(".jpeg")]
    intnumbs = []
    for file in images_list:
        intnumbs.append(file[: file.find(".")])
    intnumbs.sort(key=int)
    return [i + ".jpeg" for i in intnumbs]
