import click
from lash import plugins as plugin_registry


def make_plugin_list_command(*, plugins_dir=None, state_file=None):
    @click.command('list')
    @click.option('--installed', '-i', is_flag=True, help='Show only installed plugins.')
    @click.option('--not-installed', '-ni', 'not_installed', is_flag=True, help='Show only uninstalled plugins.')
    def plugin_list(installed, not_installed):
        """List plugins and their install status."""
        available = plugin_registry.get_available_plugins(plugins_dir=plugins_dir)
        active_cmds = set(
            plugin_registry.get_lazy_commands(plugins_dir=plugins_dir, state_file=state_file).keys()
        )

        found_any = False
        for plugin_name in sorted(available.keys()):
            manifest = available[plugin_name]
            cmds = manifest['commands']
            active_count = sum(1 for c in cmds if c in active_cmds)

            is_any_active = active_count > 0
            is_fully_active = active_count == len(cmds)
            is_not_installed = active_count == 0

            if installed and not is_any_active:
                continue
            if not_installed and not is_not_installed:
                continue

            found_any = True
            click.echo(f"  {plugin_name}")
            for cmd_name, cmd_info in cmds.items():
                marker = '+' if cmd_name in active_cmds else '-'
                click.echo(f"    {marker} {cmd_name:<16} {cmd_info['description']}")
            click.echo()

        if not found_any:
            if installed:
                click.echo("No plugins installed.")
                click.echo("Run 'lash plugin add <plugin>' to install.")
            elif not_installed:
                click.echo("All available plugins are installed.")

    return plugin_list


# Backward-compatible alias used by tests
make_plugins_command = make_plugin_list_command
