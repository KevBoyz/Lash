# Lash Project - Agent Onboarding Guide

## Entry Points & Architecture

**Main Entry**: Run `python -m lash` or `lash` to invoke the CLI

**Core Files**:
- `lash/__init__.py` - Registers Global CLI group + plugin command
- `lash/__main__.py` - Entry point from command line
- `lash/core/lazy_group.py` - LazyGroup: defers module import until command invoked
- `lash/core/plugin_manager.py` - Plugin CLI: add, remove, list + plugin group

**Plugin Structure**:
- Plugins: `lash/plugins/<name>/` (audio, calc, crack, device, file, image, monitor, random, sched, spider, video, web, work)
- Files: `cli.py` (Click entry points), `core.py` (business logic), `helpers.py` (utilities)
- All plugins have `manifest.json` at root

## Plugin System

**Manifest Fields** (`manifest.json`):
- `name`: plugin identifier matching directory name
- `category`: display group in `plugin list`
- `core: true`: always-on plugins (crack, random)
- `commands`: map of `cmd_name → {module, description, requires}`
- `module`: import path like `lash.plugins.<name>.cli:<obj>)

**State Files**:
- `~/.lash/installed.json` - Tracks installed/removed commands
- `~/.lash/data/<plugin>/` - Plugin data storage

**Plugin Loading**:
- Commands discovered via `plugins/__init__.py` scanning `manifest.json` at runtime
- Plugin data stored in user home dir: `~/.lash/data/<plugin>/`

## Commands

**Core Commands**:
```bash
lash --help                  # List all commands
 lash plugin list [-i|-ni]   # List plugins by category + install status
 lash plugin add <plugin>... # Install one or more plugins
 lash plugin remove <plugin>... # Uninstall one or more plugins
```

**Plugin Commands**:
- Every plugin contributes its own commands (e.g., `work add`, `work rm`, `work start`)
- All commands lazy-loaded: plugins deferred import until first invoked

## Development Structure

**File Hierarchy** (Required):
1. `cli.py` - Click entry points, output only (print/click.echo)
2. `core.py` - Business logic (no print statements)
3. `helpers.py` - Small utilities (only if core.py needs it)

**Dependencies**: `cli.py → core.py → helpers.py` (never inverted)

**Plugin Creation Steps** (RUNNING.md
try):
1. Add plugin directory under `lash/plugins/<plugin_name>/`
2. Create `manifest.json` with name, category, commands
3. Implement `cli.py` for Click entry points
4. Create `core.py` for business logic (if needed)
5. Create `helpers.py` for utilities (if core.py needs it)

## Testing

**Test Structure**:
- `pytest tests/` - Tests for lash/core/ modules
- `pytest lash/plugins/<name>/tests/` - Tests for specific plugins

**Testing Conventions**:
- Framework: pytest
- One class per tested feature (`class TestFeatureName`)
- Method names describe scenarios (`test_retorna_erro_quando_fc_maior_que_pc`)
- Imports inside test methods (no module-level imports)
- `tmp_path` fixture for filesystem operations — never touch real `~/.lash/`

**Test Execution**:
- Windows: `py -m pytest` 
- Linux/macOS: `python -m pytest`
- Run only when explicitly requested (no automatic test execution)

**Test Usage Examples**:
```bash
# Test core lash functionality
python -m pytest tests/
# Test specific plugin
python -m pytest lash/plugins/work/tests/
```

## Development Environment

**Setup**:
1. `git clone https://github.com/KevBoyz/Lash`
2. `cd Lash`
3. `python -m venv .venv`
4. `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Linux/macOS)
5. `pip install -e .` (core) or `pip install -e ".[all]"` (all optional tools)

**Environment Quirks**:
- Windows commands use PowerShell syntax, Linux/macOS use bash
- All Python commands must run in the project's `.venv` directory
- Never install packages globally when tests fail
- `lick` module must be up to date

## CI/CD & Build

**Workflows** (`.github/workflows/`):
- `python-package.yml` - Tests on push/PR: runs lint, tests
- `python-publish.yml` - Publish to PyPI on tags

**Build Commands**:
```bash
pip install build
python -m build

# Package structure in dist/
dist/
├── lash-1.3.0.tar.gz
└── lash-1.3.0-py3-none-any.whl
```

**Publish to PyPI**:
```bash
pip install twine
twine upload dist/*
```

## Runtime & Plugin Installation

**Install Plugins**:
```bash
# Lists available plugins
lash plugin list

# Install plugins
lash plugin add spy calc

# Remove plugins  
lash plugin remove calc
```

**Available Plugins** (from README.md | Current Plugins):
| Name    | Category          | Commands              |
|---------|-------------------|-----------------------|
| audio   | Audio Handlers    | audio                 |
| calc    | Calculation Tools | calc                  |
| crack   | Crack Tools       | crack (core)          |
| device  | Device Automation | autoclick, keyhold, keylogger |
| file    | File Tools        | organize, zip, crypt          |
| image   | Image Tools       | image                         |
| monitor | System Monitor    | monitor                       |
| random  | Random Generators | random (core)                 |
| sched   | Task Scheduler    | sched                         |
| spider  | Spider Tools      | web, seeker                   |
| video   | Video Tools       | video                 |
| web     | Web Tools         | web                   |
| work    | Work Tracker      | work                  |

**Install New Plugins**:
1. Fork the repository
2. Create feature branch
3. Add plugin manifest at `lash/plugins/<plugin_name>/manifest.json`
4. Implement commands in appropriate modules
5. Open pull request

**Plugin Manifest Format**:
```json
{
  "name": "my_plugin",
  "description": "Short description shown in lash plugins --available",
  "commands": {
    "mycommand": {
      "module": "lash.my_module:my_function",
      "description": "What this command does",
      "requires": ["some-package>=1.0.0"]
    }
  }
}
```

## Agent Pitfalls

**Things agents commonly miss**:

1. **Command execution**: Always use Windows PowerShell commands, never use bash-style pipes
2. **Tests**: Never run tests automatically during development
3. **Plugin hierarchy**: `helpers.py` only exists if `core.py` needs it — check before using
4. **Data storage**: Use `~/.lash/data/<plugin>/` not CWD or `~/.lash/` directly
5. **Plugin registration**: Plugins always-on if `core: true` in manifest, regardless of install status
6. **Python environment**: All commands must run in project `.venv`, never global Python
7. **Click version**: `click>=8.1.3` required
8. **Manifest fields**: `name` must match directory name exactly
9. **Install order**: Run `pip install -e .` before installing optional deps with `[all]`
10. **CI warnings**: Windows tests use `.venv\Scripts\python.exe` pattern
