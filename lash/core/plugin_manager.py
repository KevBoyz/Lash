import re
import subprocess
import sys
from collections import defaultdict
import click
from rich.console import Console
from lash import plugins as plugin_registry

_console = Console()


def _package_name(requirement):
    return re.split(r'[><=!]', requirement)[0].strip()


def make_download_command(*, plugins_dir=None, state_file=None):  # noqa: C901
    @click.command('add')
    @click.argument('plugins', nargs=-1, required=False)
    @click.option('-a', '--all', 'install_all', is_flag=True, help='Install all missing plugins')
    def add(plugins, install_all):
        """Add one or more plugins."""
        available = plugin_registry.get_available_plugins(plugins_dir=plugins_dir)

        if install_all:
            plugins = list(available.keys())
        elif not plugins:
            raise click.UsageError("Missing argument 'PLUGIN' or use -a to install all.")

        for plugin_name in plugins:
            if plugin_name not in available:
                click.echo(f"Unknown plugin: {plugin_name}")
                click.echo(f"Available: {', '.join(sorted(available.keys()))}")
                raise SystemExit(1)

        installed_count = 0
        for plugin_name in plugins:
            try:
                _install_plugin(plugin_name, available, state_file)
                installed_count += 1
            except Exception as e:
                click.echo(f"Failed to install {plugin_name}: {e}")

        if installed_count:
            click.echo("Done. Try: lash <command> --help")
        else:
            click.echo("No plugins were installed.")

    return add


def _install_plugin(plugin_name, available, state_file):  # noqa: C901
    already_installed = set(
        plugin_registry._load_state(state_file).get('installed_commands', {}).keys()
    )
    commands_to_install = {
        cmd_name: cmd_info
        for cmd_name, cmd_info in available[plugin_name]['commands'].items()
        if cmd_name not in already_installed
    }
    if not commands_to_install:
        click.echo(f"Plugin '{plugin_name}' already installed.")
        return

    requires = list({
        req
        for cmd_info in commands_to_install.values()
        for req in cmd_info.get('requires', [])
    })

    if requires:
        with _console.status(f"Installing dependencies for {plugin_name}: {', '.join(requires)}", spinner="dots"):
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install'] + requires,
                capture_output=True,
                text=True,
            )
        if result.returncode != 0:
            raise RuntimeError(f"Dependency install failed:\n{result.stderr}")

    for cmd_name, cmd_info in commands_to_install.items():
        plugin_registry.mark_command_installed(
            cmd_name, plugin_name, cmd_info.get('requires', []), state_file=state_file
        )
    click.echo(f"Installed: {plugin_name}")


download = make_download_command()


def _list_installed_plugins(available, state_file):
    state = plugin_registry._load_state(state_file)
    installed_cmds = state.get('installed_commands', {})
    removed_cmds = set(state.get('removed_commands', []))
    installed = []
    for name, manifest in available.items():
        is_core = manifest.get('core', False)
        if is_core:
            any_installed = any(
                cmd not in removed_cmds for cmd in manifest['commands']
            )
            if any_installed:
                installed.append(name)
        else:
            any_installed = any(
                cmd in installed_cmds for cmd in manifest['commands']
            )
            if any_installed:
                installed.append(name)
    if installed:
        click.echo(f"Installed: {', '.join(sorted(installed))}")
    else:
        click.echo("No plugins installed.")


def make_remove_command(*, plugins_dir=None, state_file=None):
    @click.command('remove')
    @click.argument('plugins', nargs=-1, required=False)
    @click.option('-a', '--all', 'remove_all', is_flag=True, help='Remove all installed plugins')
    def remove(plugins, remove_all):
        """Remove one or more plugins."""
        available = plugin_registry.get_available_plugins(plugins_dir=plugins_dir)

        if remove_all:
            plugins = list(available.keys())
        elif not plugins:
            raise click.UsageError("Missing argument 'PLUGIN' or use -a to remove all.")

        commands_to_remove = _collect_remove_commands(available, plugins, state_file)

        if not commands_to_remove:
            click.echo("Nothing to remove — no commands are installed.")
            return

        _execute_remove(commands_to_remove, state_file, plugins_dir)
        click.echo("Done.")

    return remove


def _collect_remove_commands(available, plugins, state_file):
    state = plugin_registry._load_state(state_file)
    installed_cmds = state.get('installed_commands', {})
    removed_cmds = set(state.get('removed_commands', []))
    commands_to_remove = set()
    for plugin_name in plugins:
        if plugin_name not in available:
            click.echo(f"Unknown plugin: {plugin_name}")
            _list_installed_plugins(available, state_file)
            raise SystemExit(1)
        manifest = available[plugin_name]
        if manifest.get('core', False):
            plugin_installed = {
                c for c in manifest['commands'].keys()
                if c not in removed_cmds
            }
        else:
            plugin_installed = {k for k, v in installed_cmds.items() if v['plugin'] == plugin_name}
        commands_to_remove.update(plugin_installed)
    return commands_to_remove


def _execute_remove(commands_to_remove, state_file, plugins_dir):
    all_orphaned = set()
    for cmd_name in commands_to_remove:
        orphaned = plugin_registry.remove_command(
            cmd_name, state_file=state_file, plugins_dir=plugins_dir
        )
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


remove = make_remove_command()


def make_plugin_list_command(*, plugins_dir=None, state_file=None):  # noqa: C901
    @click.command('list')
    @click.option('--installed', '-i', is_flag=True, help='Show only installed plugins.')
    @click.option('--not-installed', '-ni', 'not_installed', is_flag=True, help='Show only uninstalled plugins.')
    def plugin_list(installed, not_installed):
        """List plugins and their install status."""
        available = plugin_registry.get_available_plugins(plugins_dir=plugins_dir)
        active_cmds = set(
            plugin_registry.get_lazy_commands(plugins_dir=plugins_dir, state_file=state_file).keys()
        )

        by_category = defaultdict(list)
        for plugin_name, manifest in available.items():
            category = manifest.get('category', plugin_name)
            by_category[category].append(manifest)

        found_any = False
        for category in sorted(by_category.keys()):
            cat_cmds = {}
            for manifest in by_category[category]:
                cat_cmds.update(manifest['commands'])

            active_count = sum(1 for c in cat_cmds if c in active_cmds)
            is_any_active = active_count > 0
            is_not_installed = active_count == 0

            if installed and not is_any_active:
                continue
            if not_installed and not is_not_installed:
                continue

            found_any = True
            click.echo(f"  {category}")
            for cmd_name, cmd_info in cat_cmds.items():
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


make_plugins_command = make_plugin_list_command


def _collect_active_requires(available, installed_cmds, removed_cmds):
    active_requires = set()
    for manifest in available.values():
        is_core = manifest.get('core', False)
        for cmd_name, cmd_info in manifest['commands'].items():
            if cmd_name in removed_cmds:
                continue
            if is_core or cmd_name in installed_cmds:
                active_requires.update(cmd_info.get('requires', []))
    return active_requires


def _sync_installed_requires(available, installed_cmds, state_file):
    for manifest in available.values():
        for cmd_name, cmd_info in manifest['commands'].items():
            if cmd_name not in installed_cmds:
                continue
            plugin_registry.mark_command_installed(
                cmd_name, manifest['name'],
                cmd_info.get('requires', []),
                state_file=state_file,
            )


def make_fix_command(*, plugins_dir=None, state_file=None):
    @click.command('fix')
    def fix():
        """Fix missing dependencies for installed plugins."""
        state = plugin_registry._load_state(state_file)
        installed_cmds = set(state.get('installed_commands', {}).keys())
        removed_cmds = set(state.get('removed_commands', []))
        available = plugin_registry.get_available_plugins(plugins_dir=plugins_dir)

        active_requires = _collect_active_requires(available, installed_cmds, removed_cmds)

        if not active_requires:
            click.echo("No dependencies to install.")
            if not installed_cmds:
                click.echo("Run 'lash plugin add <plugin>' first.")
            return

        click.echo(f"Checking dependencies: {', '.join(sorted(active_requires))}")

        with _console.status("Installing missing dependencies...", spinner="dots"):
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install'] + list(active_requires),
                capture_output=True,
                text=True,
            )

        if result.returncode != 0:
            _console.print(f"[red]Dependency install failed:[/red]\n{result.stderr}")
            raise SystemExit(1)

        _sync_installed_requires(available, installed_cmds, state_file)

        click.echo("Done. All plugin dependencies are now installed.")

    return fix


fix = make_fix_command()


def make_plugin_group(*, plugins_dir=None, state_file=None):
    @click.group('plugin')
    def plugin_group():
        """Manage lash plugins: add, remove, list, fix."""

    plugin_group.add_command(make_download_command(plugins_dir=plugins_dir, state_file=state_file))
    plugin_group.add_command(make_remove_command(plugins_dir=plugins_dir, state_file=state_file))
    plugin_group.add_command(make_plugin_list_command(plugins_dir=plugins_dir, state_file=state_file))
    plugin_group.add_command(fix)
    return plugin_group


plugin = make_plugin_group()
