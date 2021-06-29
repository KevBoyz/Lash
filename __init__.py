from click import group
from file_handler import *
from app_math import *
from ExtraTools import *
from webTools import *
from logger import *



@group('global')
def Global():
    ...


# Global Commands
Global.add_command(random)
Global.add_command(organize)


# Groups declaration
Global.add_command(sched)
Global.add_command(log)
Global.add_command(web)
Global.add_command(Zip)
Global.add_command(calc)








Global()
