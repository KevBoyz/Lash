import click, os
from PIL import Image
from lash.Exportables.fileTools import *
from lash.Exportables.imageTools import *


@click.group('image', help='Massive Image Handler')
def image():
    ...


@image.command(help='Flip a image')
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.option('-all', type=click.STRING, help='Edit all images on path with x extension Ex: -all ".png" ')
@click.option('-lr', is_flag=True, help='Mirror left to right')
@click.option('-tb', is_flag=True, help='Mirror top to bottom')
def flip(path, all, lr, tb):
    if not lr and not tb:
        print('Error, none action received, send some option, --help for more details')
    if all:
        _type = all  # Semantic var
        n_editions = 0  # Files modded
        os.chdir(path)
        for root, folders, files in os.walk('.'):
            for file in files:
                if file.endswith(_type):
                    if lr:
                        flipp(Image.open(os.path.join(root, file)), file, lr=True)
                    elif tb:
                        flipp(Image.open(os.path.join(root, file)), file, tb=True)
                    n_editions += 1
        print(f'Process Completed, {n_editions} files edited')
    else:
        file = get_file(path)
        im = Image.open(file)
        if lr:
            flipp(im, file, lr=True)
        elif tb:
            flipp(im, file, tb=True)



