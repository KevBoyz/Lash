import click
import os
from lash.Exportables.config import config

config = config()


@click.group('web', help='Generic Web-Tools')
def web():
    ...


@web.command()
@click.argument('path', metavar='<destiny>', type=click.Path(exists=True), default='.', required=False)
def new(path):
    '''Start a new web project

    \b
    This command will create html5, css3 and javascript files in the destination folder
    You can also edit the files code in the config.py file, to find the location of this
    archive use the getConfig, in the file, you will receive more instructions
    '''
    os.chdir(path)
    index = open('index.html', 'w')
    index.write(config['html_code'])
    index.close()
    print('Files Generated')
