import click
from lash.core.lazy_group import LazyGroup
from lash.core.downloader import download
from lash.core.remover import remove
from lash.core.plugin_list import plugins
from lash import plugins as plugin_registry


@click.group(
    name='lash',
    cls=LazyGroup,
    lazy_subcommands=plugin_registry.get_lazy_commands(),
)
def Global():
    """\b
        - Lash 1.2.7 by KevBoyz ~ https://github.com/KevBoyz/Lash
    """


Global.add_command(download)
Global.add_command(remove)
Global.add_command(plugins)
