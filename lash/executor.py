from lash.Exportables.config import config
from playsound2 import playsound
import os

config = config()


def path_type():
    if os.name == 'nt':
        return '\\'
    else:
        return '//'


def adf_path(file):
    return os.path.abspath(os.path.dirname(__file__)) + path_type() + os.path.join('additional_files', file)


def playbp():
    if config['beep']:
        playsound(adf_path('beep.wav'))
