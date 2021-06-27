from click import group
from file_handler import *
from app_math import *
from ExtraTools import *
from webTools import *



@group('global')
def Global():
    ...


# Groups declaration
Global.add_command(calc)
Global.add_command(Zip)
Global.add_command(sched)
Global.add_command(web)


# Global Commands
Global.add_command(random)
Global.add_command(organize)




Global()
