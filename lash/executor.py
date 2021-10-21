from lash.Exportables.config import config
import os

config = config()


def path_type():
    if os.name == 'nt':
        return '\\'
    else:
        return '//'


def abs_path_config():
    return os.path.abspath(os.path.dirname(__file__)) + path_type() + os.path.join('Exportables', 'config.py')
