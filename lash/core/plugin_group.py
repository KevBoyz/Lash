import click
from lash.core.plugin_list import make_plugin_list_command
from lash.core.downloader import make_download_command
from lash.core.remover import make_remove_command


def make_plugin_group(*, plugins_dir=None, state_file=None):
    @click.group('plugin')
    def plugin():
        """Manage lash plugins: add, remove, list."""

    plugin.add_command(make_download_command(plugins_dir=plugins_dir, state_file=state_file))
    plugin.add_command(make_remove_command(plugins_dir=plugins_dir, state_file=state_file))
    plugin.add_command(make_plugin_list_command(plugins_dir=plugins_dir, state_file=state_file))
    return plugin


plugin = make_plugin_group()
