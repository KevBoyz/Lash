from click import group
from file_handler import *
from app_math import *
from ExtraTools import *




@group('global')
def Global():
    ...


# Groups declaration
Global.add_command(calc)
Global.add_command(Zip)
Global.add_command(sched)

# Global Commands
Global.add_command(random)
Global.add_command(organize)




Global()
