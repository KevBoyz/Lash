import click
import os
import zipfile as zip
from lash.executor import adf_path


@click.group('web', help='Generic Web-Tools')
def web():
    ...


@web.command(help='Start a new web project')
@click.argument('path', metavar='<destiny>', type=click.Path(exists=True), default='.', required=False)
def new(path):
    web_pkg = zip.ZipFile(adf_path('web_pkg.zip'))
    os.chdir(path)
    print(adf_path('web_pkg.zip'))
    web_pkg.extractall()
    print('Files extracted ')
