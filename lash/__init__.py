from click import group
from lash.file_handler import *
from lash.image_handler import *
from lash.audio_handler import *
from lash.video_handler import *
from lash.app_math import *
from lash.webTools import *
from lash.ExtraTools import *



@group('global')
def Global():
    """\b
        - Lash 1.2.3 by KevBoyz ~ https://github.com/KevBoyz/Lash
    """
    ...


# Global Commands
Global.add_command(getConfig)
Global.add_command(random)
Global.add_command(organize)
Global.add_command(autoclick)
Global.add_command(keyhold)
Global.add_command(taskkiller)
Global.add_command(monitor)
Global.add_command(manege)

# Groups declaration
Global.add_command(sched)
Global.add_command(spy)
Global.add_command(web)
Global.add_command(Zip)
Global.add_command(image)
Global.add_command(calc)
Global.add_command(yt)
Global.add_command(video)
Global.add_command(audio)

Global()
