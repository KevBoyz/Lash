import click, os
from PIL import Image
from lash.Exportables.fileTools import *
from lash.Exportables.imageTools import *


@click.group('image', help='Massive Image Handler')
def image():
    ...


@image.command(help='Flip image(s)')
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.option('-all', type=click.STRING, help='Edit all images on path with x extension Ex: -all ".png" ')
@click.option('-lr', is_flag=True, help='Mirror left to right')
@click.option('-tb', is_flag=True, help='Mirror top to bottom')
def flip(path, all, lr, tb):
    if not lr and not tb:
        print('Error, none action received, send some option, --help for more details')
    if all:
        _type = all
        n_editions = 0
        os.chdir(path)
        for root, folders, files in os.walk('.'):
            for file in files:
                if file.endswith(_type):
                    if lr:
                        f_flip(Image.open(os.path.join(root, file)), file, lr=True)
                    elif tb:
                       f_flip(Image.open(os.path.join(root, file)), file, tb=True)
                    n_editions += 1
        print(f'Process Completed, {n_editions} files edited')
    else:
        file = get_file(path)
        im = Image.open(file)
        if lr:
            f_flip(im, file, lr=True)
        elif tb:
            f_flip(im, file, tb=True)
        print('Process completed')


@image.command(help='Resize image(s)')
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.option('-axis', nargs=2, type=click.INT, help='Set new values for x, y as you want: -axis 400 300')
@click.option('-d', is_flag=True, help='Double image size')
@click.option('-r', is_flag=True, help='Reduce image size (size / 2)')
@click.option('-all', type=click.STRING, help='Edit all images on path with x extension Ex: -all ".png" ')
def resize(path, axis, d, r, all):
    if all:
        _type = all
        n_editions = 0
        os.chdir(path)
        for root, folders, files in os.walk('.'):
            for file in files:
                if file.endswith(_type):
                    re_size(Image.open(os.path.join(root, file)), file, axis, d, r)
                    n_editions += 1
        print(f'Process completed, {n_editions} files edited')
    else:
        file = get_file(path)
        im = Image.open(file)
        re_size(im, file, axis, d, r)
        print('Process completed')



