import subprocess
import sys
import click
from lash import plugins as plugin_registry


def make_download_command(*, plugins_dir=None, state_file=None):
    @click.command('download')
    @click.argument('plugin')
    @click.option('--only', multiple=True, metavar='CMD', help='Install only these commands from the plugin.')
    def download(plugin, only):
        """Install a lash plugin. Use --only to select individual commands."""
        available = plugin_registry.get_available_plugins(plugins_dir=plugins_dir)

        if plugin not in available:
            click.echo(f"Unknown plugin: {plugin}")
            click.echo(f"Available: {', '.join(sorted(available.keys()))}")
            raise SystemExit(1)

        manifest = available[plugin]
        all_plugin_commands = manifest['commands']

        if only:
            unknown = set(only) - set(all_plugin_commands.keys())
            if unknown:
                click.echo(f"Unknown command(s) in {plugin}: {', '.join(sorted(unknown))}")
                click.echo(f"Commands in {plugin}: {', '.join(sorted(all_plugin_commands.keys()))}")
                raise SystemExit(1)
            target_commands = {k: v for k, v in all_plugin_commands.items() if k in only}
        else:
            target_commands = all_plugin_commands

        already_installed = set(
            plugin_registry._load_state(state_file).get('installed_commands', {}).keys()
        )
        commands_to_install = {
            k: v for k, v in target_commands.items() if k not in already_installed
        }

        if not commands_to_install:
            click.echo(f"All selected commands already installed.")
            return

        all_requires = list({
            req
            for cmd_info in commands_to_install.values()
            for req in cmd_info.get('requires', [])
        })

        if all_requires:
            click.echo(f"Installing dependencies...")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install'] + all_requires,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                click.echo(f"Dependency install failed:\n{result.stderr}")
                raise SystemExit(1)

        for cmd_name, cmd_info in commands_to_install.items():
            plugin_registry.mark_command_installed(
                cmd_name,
                plugin,
                cmd_info.get('requires', []),
                state_file=state_file,
            )
            click.echo(f"  + {cmd_name}")

        click.echo(f"Done. Try: lash <command> --help")

    return download


download = make_download_command()
