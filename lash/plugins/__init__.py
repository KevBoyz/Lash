import hashlib
import importlib.metadata
import json
import os
import pathlib
import re
import sys
import tomllib
from functools import cache

_DEFAULT_PLUGINS_DIR = pathlib.Path(__file__).parent
_PYPROJECT = pathlib.Path(__file__).parents[2] / "pyproject.toml"


def _env_state_file():
    """State file of the current Python environment (venv or global).

    Each environment keeps its own state so plugins added or removed in one
    venv don't leak into another one.
    """
    prefix = os.path.normcase(os.path.realpath(sys.prefix))
    env_id = hashlib.sha256(prefix.encode()).hexdigest()[:16]
    return pathlib.Path.home() / ".lash" / "envs" / f"{env_id}.json"


_DEFAULT_STATE_FILE = _env_state_file()


def _load_state(state_file):
    state_file = pathlib.Path(state_file or _DEFAULT_STATE_FILE)
    if not state_file.exists():
        return {"installed_commands": {}}
    try:
        return json.loads(state_file.read_text())
    except (json.JSONDecodeError, AttributeError):
        return {"installed_commands": {}}


def _save_state(state, state_file):
    state_file = pathlib.Path(state_file or _DEFAULT_STATE_FILE)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2))


def _normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def requirement_name(requirement):
    """'Pillow>=9.3.0' -> 'pillow'; 'markdown-it-py (>=2.2.0)' -> 'markdown-it-py'."""
    name = re.split(r"[\s\[(<>=!~;@]", requirement.strip(), maxsplit=1)[0]
    return _normalize(name)


def is_package_installed(requirement):
    try:
        importlib.metadata.distribution(requirement_name(requirement))
    except importlib.metadata.PackageNotFoundError:
        return False
    return True


def requirements_satisfied(requires):
    return all(is_package_installed(req) for req in requires)


def is_command_active(cmd_name, cmd_info, is_core, removed_cmds):
    """Core commands and commands whose deps are all present are active."""
    if cmd_name in removed_cmds:
        return False
    return is_core or requirements_satisfied(cmd_info.get("requires", []))


def _is_extra(requirement):
    return re.search(r";.*\bextra\s*==", requirement) is not None


def _lash_requirements():
    try:
        requires = importlib.metadata.requires("lash") or []
    except importlib.metadata.PackageNotFoundError:
        project = tomllib.loads(_PYPROJECT.read_text())["project"]
        requires = project["dependencies"]
    return [req for req in requires if not _is_extra(req)]


@cache
def protected_packages():
    """Lash and its base deps (transitively). Never uninstalled by plugins."""
    protected = {"lash"}
    pending = [requirement_name(req) for req in _lash_requirements()]
    while pending:
        name = pending.pop()
        if name in protected:
            continue
        protected.add(name)
        try:
            requires = importlib.metadata.requires(name) or []
        except importlib.metadata.PackageNotFoundError:
            continue
        pending.extend(
            requirement_name(req) for req in requires if not _is_extra(req)
        )
    return frozenset(protected)


def get_available_plugins(*, plugins_dir=None):
    plugins_dir = pathlib.Path(plugins_dir or _DEFAULT_PLUGINS_DIR)
    plugins = {}
    for entry in plugins_dir.iterdir():
        if not entry.is_dir():
            continue
        manifest_file = entry / "manifest.json"
        if not manifest_file.exists():
            continue
        manifest = json.loads(manifest_file.read_text())
        plugins[manifest["name"]] = manifest
    return plugins


def get_lazy_commands(*, plugins_dir=None, state_file=None):
    state = _load_state(state_file)
    removed_cmds = set(state.get("removed_commands", []))
    available = get_available_plugins(plugins_dir=plugins_dir)

    commands = {}
    for manifest in available.values():
        is_core = manifest.get("core", False)
        for cmd_name, cmd_info in manifest["commands"].items():
            if is_command_active(cmd_name, cmd_info, is_core, removed_cmds):
                commands[cmd_name] = {
                    "module": cmd_info["module"],
                    "description": cmd_info["description"],
                }
    return commands


def mark_command_installed(
        cmd_name,
        plugin_name,
        requires,
        *,
        state_file=None):
    state = _load_state(state_file)
    if "installed_commands" not in state:
        state["installed_commands"] = {}
    state["installed_commands"][cmd_name] = {
        "plugin": plugin_name,
        "requires": requires,
    }
    if "removed_commands" in state and cmd_name in state["removed_commands"]:
        state["removed_commands"].remove(cmd_name)
    _save_state(state, state_file)


def _still_needed(available, installed, removed_cmds):
    needed = set(protected_packages())
    for info in installed.values():
        needed.update(requirement_name(req) for req in info["requires"])
    for manifest in available.values():
        is_core = manifest.get("core", False)
        for cmd_name, cmd_info in manifest["commands"].items():
            if is_command_active(cmd_name, cmd_info, is_core, removed_cmds):
                needed.update(
                    requirement_name(req)
                    for req in cmd_info.get("requires", [])
                )
    return needed


def remove_commands(cmd_names, *, state_file=None, plugins_dir=None):
    """Mark commands as removed. Returns now-orphaned dep strings.

    Only deps lash installed for the removed commands can be orphaned, and
    never lash's own base deps (click, rich, ...). Orphans are computed after
    the whole batch is removed, so deps shared inside the batch are freed too.
    """
    state = _load_state(state_file)
    installed = state.setdefault("installed_commands", {})
    removed = state.setdefault("removed_commands", [])
    available = get_available_plugins(plugins_dir=plugins_dir)
    manifest_cmds = {
        cmd for manifest in available.values() for cmd in manifest["commands"]
    }

    candidates = []
    changed = False
    for cmd_name in cmd_names:
        if cmd_name not in installed and cmd_name not in manifest_cmds:
            continue
        changed = True
        if cmd_name not in removed:
            removed.append(cmd_name)
        info = installed.pop(cmd_name, None)
        if info:
            candidates.extend(info["requires"])
    if changed:
        _save_state(state, state_file)
    if not candidates:
        return []

    still_needed = _still_needed(available, installed, set(removed))
    return sorted({
        req for req in candidates
        if requirement_name(req) not in still_needed
    })


def remove_command(cmd_name, *, state_file=None, plugins_dir=None):
    return remove_commands(
        [cmd_name], state_file=state_file, plugins_dir=plugins_dir)
