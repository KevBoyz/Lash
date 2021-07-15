from click import group
from file_handler import *
from app_math import *
from ExtraTools import *
from webTools import *
from ExtraTools.logger import *



@group('global')
def Global():
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
