import click
import lash.plugins as plugin_registry
from lash.core.lazy_group import LazyGroup
from lash.core.plugin_manager import plugin


@click.group(
    name='lash',
    cls=LazyGroup,
    lazy_subcommands=plugin_registry.get_lazy_commands(),
)
def Global():
    """\b
        - Lash 1.3.0 by KevBoyz ~ https://github.com/KevBoyz/Lash
    """


Global.add_command(plugin)
