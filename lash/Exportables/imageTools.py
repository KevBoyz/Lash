import matplotlib.pyplot as plt
from PIL import Image, ImageEnhance
from lash.Exportables.fileTools import *

# Local functions


def sharp(im, v):
    im = ImageEnhance.Sharpness(im)
    return im.enhance(v)


def color(im, v):
    im = ImageEnhance.Color(im)
    return im.enhance(v)


def contrast(im, v):
    im = ImageEnhance.Contrast(im)
    return im.enhance(v)


def brightness(im, v):
    im = ImageEnhance.Brightness(im)
    return im.enhance(v)


# Exportable functions


def save(im, file):
    try:
        im.save(file)
    except ValueError as e:  # unknown file extension
        print(f'Error: {e}')


def compare(im, mod_im):
    plt.figure(facecolor='#cccccc')
    plt.suptitle('\n\n\nImages comparison')

    plt.subplot(1, 2, 1)
    plt.title('Original')
    plt.imshow(im)

    plt.subplot(1, 2, 2)
    plt.title('Edited')
    plt.imshow(mod_im)

    plt.show()


# Exportable editors


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


def adjust_exec(im, contrast_v, brightness_v, color_v, sharpness_v):
    im = contrast(im, contrast_v)
    im = brightness(im, brightness_v)
    im = color(im, color_v)
    im = sharp(im, sharpness_v)
    return color(im, 1)  # Return the iterable obj, this func does nothing with img


