import matplotlib.pyplot as plt
from PIL import Image, ImageEnhance, ImageFilter, ImageFont, ImageDraw
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


def f_flip(im, file, c, t, lr=False, tb=False):
    if not c:
        c = True if t else None
    if lr:
        im_flipped = im.transpose(Image.FLIP_LEFT_RIGHT)
        compare(im, im_flipped) if c else None
        if not t:
            save(im_flipped, file)
    elif tb:
        im_flipped = im.transpose(Image.FLIP_TOP_BOTTOM)
        save(im_flipped, file) if not t else None


def re_size(im, file, root, axis, d, r, c, t):
    if not axis and not d and not r:
        print('Error, none action received, send some option, --help for more details')
    else:
        if not c:
            c = True if t else None
        if axis:
            x, y = axis
            im_rszd = im.resize((x, y))
            compare(im, im_rszd) if c else None
            save(im_rszd, os.path.join(root, file)) if not t else None
        elif d:
            im_rszd = im.resize((int(im.size[0] * 2), int(im.size[1] * 2)))
            compare(im, im_rszd) if c else None
            save(im_rszd, os.path.join(root, file)) if not t else None
        elif r:
            im_rszd = im.resize((int(im.size[0] / 2), int(im.size[1] / 2)))
            compare(im, im_rszd) if c else None
            save(im_rszd, os.path.join(root, file)) if not t else None


def adjust_exec(im, contrast_v, brightness_v, color_v, sharpness_v):
    im = contrast(im, contrast_v)
    im = brightness(im, brightness_v)
    im = color(im, color_v)
    im = sharp(im, sharpness_v)
    return color(im, 1)  # Return the iterable obj, this func does nothing with img


def filter_apply(im, file, root, t, c, b, co, d, e, k):
    if not c:
        c = True if t else None
    mod_im = im.copy()
    if b:
        mod_im = mod_im.filter(ImageFilter.BLUR)
    if co:
        mod_im = mod_im.filter(ImageFilter.CONTOUR)
    if d:
        mod_im = mod_im.filter(ImageFilter.DETAIL)
    if e:
        mod_im = mod_im.filter(ImageFilter.EMBOSS)
    if k:
        mod_im = contrast(mod_im, 1.1)
        mod_im = sharp(im, 1.1)
        mod_im = brightness(mod_im, 1.1)
        mod_im = color(mod_im, 1.3)
        compare(im, color(mod_im, 1)) if c else None
    if not k:
        compare(im, mod_im) if c else None
    save(mod_im, os.path.join(root, file)) if not t else None


def wmarke(text, file, root, im, c, t, tp, ts, tc, tf, axis):
    if os.name != 'nt':
        print('Sorry, this command are not available for your operational system')
        return
    if tf[-4:] != '.ttf':
        tf = tf + '.ttf'
    try:
        font = ImageFont.truetype(os.path.join('C:\\', 'Windows', 'Fonts', tf), size=ts)
        mod_im = im.copy()
        draw = ImageDraw.Draw(mod_im)
        if not axis:
            pxlen = len(text) * ts
            x = ((mod_im.size[0] - pxlen) + pxlen / 2.5) - tp + 5
            y = mod_im.size[1] / 10 - 15
            if y < ts + tp:
                while y < ts + tp:
                    y += tp
            draw.text((x, mod_im.size[1] - y), text, font=font, fill=tc)
        else:
            x, y = axis
            draw.text((x, y), text, font=font, fill=tc)
        if not c:
            c = True if t else None
        compare(im, mod_im) if c else None
        save(mod_im, os.path.join(root, file)) if not t else None
    except OSError:
        print('Error: Font not valid, try use arial or ebrima. --help for details')
