import json
import pathlib

_DEFAULT_PLUGINS_DIR = pathlib.Path(__file__).parent
_DEFAULT_STATE_FILE = pathlib.Path.home() / '.lash' / 'installed.json'


def _load_state(state_file):
    state_file = pathlib.Path(state_file or _DEFAULT_STATE_FILE)
    if not state_file.exists():
        return {'installed_commands': {}}
    try:
        return json.loads(state_file.read_text())
    except (json.JSONDecodeError, AttributeError):
        return {'installed_commands': {}}


def get_available_plugins(*, plugins_dir=None):
    plugins_dir = pathlib.Path(plugins_dir or _DEFAULT_PLUGINS_DIR)
    plugins = {}
    for entry in plugins_dir.iterdir():
        if not entry.is_dir():
            continue
        manifest_file = entry / 'manifest.json'
        if not manifest_file.exists():
            continue
        manifest = json.loads(manifest_file.read_text())
        plugins[manifest['name']] = manifest
    return plugins


def get_lazy_commands(*, plugins_dir=None, state_file=None):
    state = _load_state(state_file)
    installed_cmds = set(state.get('installed_commands', {}).keys())
    available = get_available_plugins(plugins_dir=plugins_dir)

    commands = {}
    for manifest in available.values():
        is_core = manifest.get('core', False)
        for cmd_name, cmd_info in manifest['commands'].items():
            if is_core or cmd_name in installed_cmds:
                commands[cmd_name] = cmd_info['module']
    return commands


def mark_command_installed(cmd_name, plugin_name, requires, *, state_file=None):
    state_file = pathlib.Path(state_file or _DEFAULT_STATE_FILE)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state = _load_state(state_file)
    if 'installed_commands' not in state:
        state['installed_commands'] = {}
    state['installed_commands'][cmd_name] = {
        'plugin': plugin_name,
        'requires': requires,
    }
    state_file.write_text(json.dumps(state, indent=2))


def remove_command(cmd_name, *, state_file=None):
    """Remove command from state. Returns list of now-orphaned dep strings."""
    state_file = pathlib.Path(state_file or _DEFAULT_STATE_FILE)
    state = _load_state(state_file)
    installed = state.get('installed_commands', {})

    if cmd_name not in installed:
        return []

    cmd_requires = set(installed[cmd_name]['requires'])
    del installed[cmd_name]

    still_needed = set()
    for info in installed.values():
        still_needed.update(info['requires'])

    orphaned = list(cmd_requires - still_needed)
    state_file.write_text(json.dumps(state, indent=2))
    return orphaned
