import click, os, zipfile as zip


@click.group('web', help='Generic Web-Tools')
def web():
    ...


@web.command(help='Start a new web project')
@click.argument('path', metavar='<destiny>', type=click.Path(exists=True))
def new(path):
    os.chdir('Packages')
    web_pkg = zip.ZipFile('web_pkg.zip', 'r')
    os.chdir(path)
    web_pkg.extractall()
    print('Files extracted successfully')