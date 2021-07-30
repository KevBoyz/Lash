from click import group
from .file_handler import *
from .app_math import *
from .webTools import *
from .ExtraTools import *



@group('global')
def Global():
    """ - Lash 1.0.0 by KevBoyz ~ https://github.com/KevBoyz/Lash"""
    ...


# Global Commands
Global.add_command(random)
Global.add_command(organize)
Global.add_command(autoclick)
Global.add_command(keyhold)


# Groups declaration
Global.add_command(sched)
Global.add_command(log)
Global.add_command(web)
Global.add_command(Zip)
Global.add_command(calc)








Global()
