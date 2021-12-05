from PIL import Image
from lash.Exportables.fileTools import *


def save(im, file):
    try:
        im.save(file)
    except ValueError as e:  # unknown file extension
        print(f'Error: {e}')


def f_flip(im, file, lr=False, tb=False):
    if lr:
        im_flipped = im.transpose(Image.FLIP_LEFT_RIGHT)
        save(im_flipped, file)
    elif tb:
        im_flipped = im.transpose(Image.FLIP_TOP_BOTTOM)
        save(im_flipped, file)


def re_size(im, file, axis, d, r):
    if not axis and not d and not r:
        print('Error, none action received, send some option, --help for more details')
        return
    else:
        if axis:
            x, y = axis
            im_rszd = im.resize((x, y))
            save(im_rszd, file)
        elif d:
            im_rszd = im.resize((int(im.size[0] * 2), int(im.size[1] * 2)))
            save(im_rszd, file)
        elif r:
            im_rszd = im.resize((int(im.size[0] / 2), int(im.size[1] / 2)))
            save(im_rszd, file)
