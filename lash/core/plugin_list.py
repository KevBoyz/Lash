import click
from lash import plugins as plugin_registry


def make_plugins_command(*, plugins_dir=None, state_file=None):
    @click.command('plugins')
    @click.option('--available', is_flag=True, help='Also show plugins available to install.')
    def plugins(available):
        """List installed plugins and commands."""
        all_plugins = plugin_registry.get_available_plugins(plugins_dir=plugins_dir)
        state = plugin_registry._load_state(state_file)
        installed_cmds = state.get('installed_commands', {})

        core_plugins = {n: m for n, m in all_plugins.items() if m.get('core')}
        user_plugins = {n: m for n, m in all_plugins.items() if not m.get('core')}

        has_any_installed = {
            v['plugin'] for v in installed_cmds.values()
        } & set(user_plugins.keys())

        fully_installed_plugin_names = {
            n for n in has_any_installed
            if all(cmd in installed_cmds for cmd in user_plugins[n]['commands'].keys())
        }

        if has_any_installed:
            click.echo("Installed:")
            for plugin_name in sorted(has_any_installed):
                manifest = user_plugins[plugin_name]
                click.echo(f"  {plugin_name}")
                for cmd_name, cmd_info in manifest['commands'].items():
                    if cmd_name in installed_cmds:
                        click.echo(f"    + {cmd_name:<16} {cmd_info['description']}")
                    else:
                        click.echo(f"    - {cmd_name:<16} (not installed)")
            click.echo()

        if core_plugins:
            click.echo("Core (always available):")
            for plugin_name in sorted(core_plugins.keys()):
                manifest = core_plugins[plugin_name]
                click.echo(f"  {plugin_name}")
                for cmd_name, cmd_info in manifest['commands'].items():
                    click.echo(f"    * {cmd_name:<16} {cmd_info['description']}")
            click.echo()

        if available:
            not_installed = {
                n: m for n, m in user_plugins.items()
                if not any(cmd in installed_cmds for cmd in m['commands'].keys())
            }
            partially_installed = {
                n: m for n, m in user_plugins.items()
                if n in has_any_installed and n not in fully_installed_plugin_names
            }

            if not_installed or partially_installed:
                click.echo("Not installed (run 'lash download <plugin>'):")
                for plugin_name in sorted(not_installed.keys()):
                    manifest = not_installed[plugin_name]
                    click.echo(f"  {plugin_name:<20} {manifest['description']}")
                for plugin_name in sorted(partially_installed.keys()):
                    manifest = partially_installed[plugin_name]
                    click.echo(f"  {plugin_name:<20} {manifest['description']} (partial)")
            else:
                click.echo("All available plugins are installed.")

        if not has_any_installed and not available:
            click.echo("No plugins installed.")
            click.echo("Run 'lash plugins --available' to see what's available.")
            click.echo("Run 'lash download <plugin>' to install.")

    return plugins


plugins = make_plugins_command()
