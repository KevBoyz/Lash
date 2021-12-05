from PIL import Image


def flipp(im, file, lr=False, tb=False):
    if lr:
        im_flipped = im.transpose(Image.FLIP_LEFT_RIGHT)
        try:
            im_flipped.save(file)
        except ValueError as e:  # unknown file extension
            print(f'Error: {e}')
    elif tb:
        im_flipped = im.transpose(Image.FLIP_TOP_BOTTOM)
        try:
            im_flipped.save(file)
        except ValueError as e:  # unknown file extension
            print(f'Error: {e}')

