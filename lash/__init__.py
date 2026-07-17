import importlib.metadata
import tomllib
from pathlib import Path

import click

import lash.plugins as plugin_registry
from lash.core.lazy_group import LazyGroup
from lash.core.plugin_manager import plugin

try:
    __version__ = importlib.metadata.version("lash")
except importlib.metadata.PackageNotFoundError:
    _pyproject = Path(__file__).parent.parent.joinpath("pyproject.toml")
    __version__ = tomllib.loads(_pyproject.read_text())["project"]["version"]


@click.group(
    name='lash',
    cls=LazyGroup,
    lazy_subcommands=plugin_registry.get_lazy_commands(),
    help=f"\b\n    - Lash {__version__} by KevBoyz ~ https://github.com/KevBoyz/Lash\n",
)
def Global():
    pass


Global.add_command(plugin)
