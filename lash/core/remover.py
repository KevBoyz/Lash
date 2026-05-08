import re
import subprocess
import sys
import click
from lash import plugins as plugin_registry


def _package_name(requirement):
    """Extract bare package name from requirement string like 'rich>=12.6.0'."""
    return re.split(r'[><=!]', requirement)[0].strip()


def make_remove_command(*, plugins_dir=None, state_file=None):
    @click.command('remove')
    @click.argument('plugin')
    @click.option('--cmd', multiple=True, metavar='CMD', help='Remove only these commands from the plugin.')
    def remove(plugin, cmd):
        """Remove an installed plugin or specific commands from it."""
        available = plugin_registry.get_available_plugins(plugins_dir=plugins_dir)

        if plugin not in available:
            click.echo(f"Unknown plugin: {plugin}")
            click.echo(f"Available: {', '.join(sorted(available.keys()))}")
            raise SystemExit(1)

        state = plugin_registry._load_state(state_file)
        installed_cmds = state.get('installed_commands', {})

        plugin_installed = {k for k, v in installed_cmds.items() if v['plugin'] == plugin}

        if cmd:
            unknown = set(cmd) - set(available[plugin]['commands'].keys())
            if unknown:
                click.echo(f"Unknown command(s) in {plugin}: {', '.join(sorted(unknown))}")
                raise SystemExit(1)
            commands_to_remove = plugin_installed & set(cmd)
        else:
            commands_to_remove = plugin_installed

        if not commands_to_remove:
            click.echo(f"Nothing to remove — no commands from {plugin} are installed.")
            return

        all_orphaned = set()
        for cmd_name in commands_to_remove:
            orphaned = plugin_registry.remove_command(cmd_name, state_file=state_file)
            all_orphaned.update(orphaned)
            click.echo(f"  - {cmd_name}")

        if all_orphaned:
            pkg_names = [_package_name(r) for r in all_orphaned]
            click.echo(f"Uninstalling orphaned dependencies: {', '.join(pkg_names)}")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'uninstall', '-y'] + pkg_names,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                click.echo(f"Warning: dependency uninstall failed:\n{result.stderr}")

        click.echo("Done.")

    return remove


remove = make_remove_command()
