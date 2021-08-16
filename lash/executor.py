from lash.Exportables.config import config
from playsound2 import playsound
import os

config = config()


def playbp():
    if config['beep']:
        playsound(os.path.abspath(os.path.dirname(__file__)) + r'/additional_files/beep.wav')