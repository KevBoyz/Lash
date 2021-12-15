import click, os
from tqdm import tqdm
from PIL import Image
from lash.Exportables.fileTools import *
from lash.Exportables.imageTools import *


@click.group('image', help='Massive Image Handler')
def image():
    ...


@image.command()
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.option('-all', is_flag=True, help='Edit all images on path')
@click.option('-c', '-compare', is_flag=True, help='Compare the original image with the edited')
@click.option('-t', '-test', is_flag=True, help='Just test the editor, don\'t save the edition')
@click.option('-lr', is_flag=True, help='Mirror left to right')
@click.option('-tb', is_flag=True, help='Mirror top to bottom')
def flip(path, all, c, t, lr, tb):
    """
    Flip Image(s)

    Flip one or all images with same extension on a folder, you can flip left to right or
    top to bottom, before do the flip, you can use the -t option to compare the original
    image with the edited without rewrite the file. Check the examples below:
    \b

    \b
    $~ lash image flip -lr -t C:\\Users\\User\\Folder\\image.png
    $~ lsh image flip -tb -all "png" C:\\Users\\User\\Folder
    """
    if not lr and not tb:
        print('Error, none action received, send some option, --help for more details')
    if all:
        n_editions = 0
        os.chdir(path)
        for root, folders, files in os.walk('.'):
            for file in files:
                try:
                    if lr:
                        f_flip(Image.open(os.path.join(root, file)), file, c=c, t=t, lr=True)
                    elif tb:
                        f_flip(Image.open(os.path.join(root, file)), file, c=c, t=t, tb=True)
                    n_editions += 1
                except:
                    pass
        print(f'Process Completed, {n_editions} files edited')
    else:
        file = get_file(path)
        im = Image.open(file)
        if lr:
            f_flip(im, file, c=c, t=t, lr=True)
        elif tb:
            f_flip(im, file, c=c, t=t, tb=True)
        print('Process completed')


@image.command()
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.option('-all', is_flag=True, help='Edit all images on path')
@click.option('-c', '-compare', is_flag=True, help='Compare the original image with the edited')
@click.option('-t', '-test', is_flag=True, help='Just test the editor, don\'t save the edition')
@click.option('-axis', nargs=2, type=click.INT, help='Set new values for x, y dimensions')
@click.option('-d', is_flag=True, help='Double image size')
@click.option('-r', is_flag=True, help='Reduce image size (size / 2)')
def resize(path, all, c, t, axis, d, r):
    """
    Resize Image(s)

    Resize one or all images with same extension on a folder, you can double or reduce by 2
    the image size respecting the proportion with -d, -r or do something more customizable defining
    a custom size (x, y) with -axis as you want. Check the examples below:
    \b

    \b
    $~ lash image resize -axis 400 300 C:\\Users\\User\\Folder\\image.png
    $~ lash image adjust -all -s 1.1 C:\\Users\\User\\Folder
    """
    if all:
        n_editions = 0
        os.chdir(path)
        for root, folders, files in os.walk('.'):
            for file in files:
                try:
                    re_size(Image.open(os.path.join(root, file)), file, axis, d, r, c, t)
                    n_editions += 1
                except:
                    pass
        print(f'Process completed, {n_editions} files edited')
    else:
        file = get_file(path)
        im = Image.open(file)
        re_size(im, file, axis, d, r, c, t)
        print('Process completed')


@image.command()
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.option('-all', is_flag=True, help='Edit all images on path')
@click.option('-c', '-compare', is_flag=True, help='Compare the original image with the edited')
@click.option('-t', '-test', is_flag=True, help='Just test the editor, don\'t save the edition')
@click.option('-ct', '-contrast', type=click.FLOAT, help='Adjust the image contrast', default=1)
@click.option('-b', '-brightness', type=click.FLOAT, help='Adjust the image brightness', default=1)
@click.option('-s', '-saturation', type=click.FLOAT, help='Adjust the image saturation', default=1)
@click.option('-sh', '-sharp', type=click.FLOAT, help='Sharp the image', default=1)
def adjust(path, all, c, t, ct, b, s, sh):
    """
    Adjust Image(s)

    Adjust one or all images with same extension on a folder. This command is a way to do a
    special edition on a specific image, the -all option is not recommended.
    \b

    You can modify the contrast, brightness, saturation or sharp the image, but ponder the
    values, all image values is 1 by default, to do a good editions, use values only between
    1 and 2. You can reduce the values passing 0, like 0.5 or 0.9. You can also check the
    edition before save the file with -t and compare the images with -c. Check the examples below:
    \b

    $~ lash image adjust -t -ct 1.2 -b 1.1 -s 1.3 C:\\Users\\Usr\\Folder\\img.png
    \b
    $~ lash image adjust -all -s 1.1 C:\\Users\\User\\Folder
    """
    if all:
        n_editions = 0
        os.chdir(path)
        for root, folders, files in os.walk('.'):
            for file in files:
                try:
                    save(adjust_exec(Image.open(os.path.join(root, file)), ct, b, s, sh), file)
                    n_editions += 1
                except:
                    pass
        print(f'Process completed, {n_editions} files edited')
    else:
        file = get_file(path)
        im = Image.open(file)
        mod_im = adjust_exec(im, ct, b, s, sh)
        c = True if t else None
        if c:
            compare(im, mod_im)
        if t:
            print('Test concluded, nothing special happens')
        else:
            save(mod_im, file)
            print('Process completed, image rewritten')


@image.command()
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.option('-all', is_flag=True, help='Edit all images on path')
@click.option('-c', '-compare', is_flag=True, help='Compare the original image with the edited')
@click.option('-t', '-test', is_flag=True, help='Just test the editor, don\'t save the edition')
@click.option('-b', '-blur', is_flag=True, help='Apply blur filter')
@click.option('-co', '-blur', is_flag=True, help='Apply contour filter')
@click.option('-d', '-blur', is_flag=True, help='Apply detail filter')
@click.option('-e', '-blur', is_flag=True, help='Apply emboss filter')
@click.option('-k', '-kbzup', '-blur', is_flag=True, help='Apply kbzup filter')
def filter(path, all, c, t, b, co, d, e, k):
    """
    Apply Filters

    Apply simple filters on images with this command. The most recommended is -k (kbzup),
    that do a simple upgrade in your image, test the filters with -t option and choose the
    better for you.
    \b

    You can use multiple filters ore just one to run the command. See below:
    \b

    $~ lash image filter -t -k C:\\Users\\Usr\\Folder\\img.png
    \b
    $~ lash image adjust -all "jpeg" -k -d -b C:\\Users\\User\\Folder
    """
    if all:
        n_editions = 0
        os.chdir(path)
        with tqdm(total=files_range()) as pbar:
            for root, folders, files in os.walk('.'):
                for file in files:
                    try:
                        filter_apply(Image.open(os.path.join(root, file)), file, root, t, c, b, co, d, e, k)
                        n_editions += 1
                    except:
                        pass
                    pbar.update(1)
        print(f'Process completed, {n_editions} images edited')
    else:
        file = get_file(path)
        im = Image.open(file)
        filter_apply(im, file, os.getcwd(), t, c, b, co, d, e, k)
        print('Process completed')
