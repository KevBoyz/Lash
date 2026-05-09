# Lash — Project Guide

CLI tool built with Click + Python. Entry point: `py -m lash`.

## Structure

```
lash/
├── __init__.py          # Registers Global CLI group + plugin command
├── __main__.py          # Entry point
├── core/
│   ├── lazy_group.py    # LazyGroup: defers module import until command invoked
│   └── plugin_manager.py# Plugin CLI: add, remove, list + plugin group
└── plugins/
    ├── __init__.py      # Registry: get_available_plugins, get_lazy_commands, mark/remove command
    └── <name>/          # One package per plugin (audio, calc, crack, device, file, ...)
        ├── manifest.json
        ├── cli.py       # Click commands/groups
        ├── core.py      # Business logic called by cli
        ├── helpers.py   # Utility functions (moved from Exportables/ExtraTools)
        └── tests/

tests/
└── core/                # Tests for lash/core/ modules
```

## Plugin System

**Discovery**: `plugins/__init__.py` scans `lash/plugins/*/manifest.json` at runtime.

**manifest.json fields**:
- `name`: plugin identifier used in `plugin add/remove` (e.g. `"audio"`)
- `category`: display group in `plugin list` (e.g. `"Audio Handlers"`)
- `core: true`: always-on, no install needed (crack, random)
- `commands`: map of `cmd_name → {module, description, requires}`
- `module`: importable path to Click object (e.g. `"lash.plugins.audio.cli:audio_group"`)

**State file**: `~/.lash/installed.json`
```json
{
  "installed_commands": { "organize": { "plugin": "file", "requires": ["rich>=12.6.0"] } },
  "removed_commands": []
}
```

**LazyGroup**: commands are loaded only when invoked — keeps startup fast.

## Commands

```
lash plugin list [-i | -ni]        # list plugins by category
lash plugin add <plugin>...        # install one or more plugins
lash plugin remove <plugin>...     # uninstall one or more plugins
```

## Tests

```
pytest tests/core/   # core plugin system tests
```

No test execution during development — run only when explicitly requested.

## Current Plugins

| Name    | Category          | Commands              |
|---------|-------------------|-----------------------|
| audio   | Audio Handlers    | audio                 |
| calc    | Calculation Tools | calc                  |
| crack   | Crack Tools       | crack (core)          |
| device  | Device Automation | autoclick, keyhold    |
| file    | File Tools        | organize, zip         |
| image   | Image Tools       | image                 |
| monitor | System Monitor    | monitor               |
| random  | Random Generators | random (core)         |
| sched   | Task Scheduler    | sched                 |
| spy     | Spy Tools         | spy                   |
| video   | Video Tools       | video                 |
| web     | Web Tools         | web                   |
| work    | Work Tracker      | work                  |
