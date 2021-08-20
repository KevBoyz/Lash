from click import group
from lash.file_handler import *
from lash.app_math import *
from lash.webTools import *
from lash.ExtraTools import *
from lash.executor import playbp


@group('global')
def Global():
    """\b
        - Lash 1.1.0 by KevBoyz ~ https://github.com/KevBoyz/Lash
        Edit the package configs manually in /Exportables/config.py"""
    ...


# Global Commands
Global.add_command(random)
Global.add_command(organize)
Global.add_command(autoclick)
Global.add_command(keyhold)
Global.add_command(taskkiller)

# Groups declaration
Global.add_command(sched)
Global.add_command(spy)
Global.add_command(web)
Global.add_command(Zip)
Global.add_command(calc)

Global()
