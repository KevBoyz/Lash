# Lazy Loading + Plugin System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate startup latency caused by eager imports of all 23 dependencies, then introduce a granular plugin system where the base install requires only `click`, each tool is installed on demand via `lash download`, and users can install individual subcommands rather than full plugins.

**Architecture:** A `LazyGroup` subclass of `click.Group` maps command names to `"module:attr"` strings and imports modules only when `get_command()` is called. Plugin manifests in `lash/plugins/<name>/manifest.json` declare each command individually with its own pip requirements. A command-centric state file at `~/.lash/installed.json` tracks which commands are enabled. Three management commands handle discovery, install, and removal with automatic orphaned-dependency cleanup.

**Tech Stack:** Python stdlib (`importlib`, `pathlib`, `json`, `subprocess`, `sys`, `re`), Click 8.x, pytest + pytest-mock for testing.

---

## Current State Analysis

### Startup bottleneck chain

```
python -m lash
  → lash/__init__.py
      line 2:  from lash.file_handler import *   → loads pyminizip, rich
      line 3:  from lash.image_handler import *  → loads Pillow, tqdm
      line 4:  from lash.audio_handler import *  → loads moviepy (SLOW)
      line 5:  from lash.video_handler import *  → loads cv2, numpy, mss, pyautogui, keyboard, moviepy (VERY SLOW)
      line 6:  from lash.web_scraping import *   → loads bs4, wikipedia, pytube, gnews, rich (SLOW)
      line 7:  from lash.ExtraTools import *
                 → lash/ExtraTools/__init__.py:
                     from .Devices import *      → loads pynput
                     from .sched_manager import * → loads schedule
                     from .monitor import *      → loads psutil, dashing
                     from .work import *         → loads pandas, matplotlib (SLOW)
                     from .app_random import *
                     from .app_math import *     → loads numpy, matplotlib (SLOW)
                     from .brute_force import *
      line 8:  from lash.spy import *            → loads pyaes, pynput
      line 37: Global()                          ← CLI executes
```

All 23 deps load even for `lash --help` or `lash random`.

### Key files and objects

| File | Python object | CLI name | Heavy deps |
|------|--------------|----------|------------|
| `lash/file_handler.py` | `organize` (ln 8), `zip_group` (ln 86) | `organize`, `zip` | pyminizip, rich |
| `lash/image_handler.py` | `image` (ln 8) | `image` | Pillow, tqdm |
| `lash/audio_handler.py` | `audio_group` (ln 7) | `audio` | moviepy |
| `lash/video_handler.py` | `video` (ln 16) | `video` | cv2, numpy, mss, moviepy, pyautogui, keyboard |
| `lash/web_scraping.py` | `web` (ln 20) | `web` | bs4, requests, wikipedia, pytube, gnews, rich |
| `lash/spy.py` | `spy` (ln 11) | `spy` | pyaes, pynput |
| `lash/ExtraTools/app_math.py` | `calc` (ln 33) | `calc` | numpy, matplotlib |
| `lash/ExtraTools/monitor.py` | `monitor` (ln 21) | `monitor` | psutil, py-dashing |
| `lash/ExtraTools/work.py` | `work` (ln 89) | `work` | pandas, matplotlib |
| `lash/ExtraTools/sched_manager.py` | `sched` (ln 40) | `sched` | schedule |
| `lash/ExtraTools/Devices/tmouse.py` | `autoclick` (ln 7) | `autoclick` | pynput |
| `lash/ExtraTools/Devices/keyboard.py` | `keyhold` (ln 6) | `keyhold` | pynput |
| `lash/ExtraTools/brute_force.py` | `crack` (ln 37) | `crack` | stdlib only |
| `lash/ExtraTools/app_random.py` | `random` (ln 52) | `random` | stdlib only |

**Critical:** `lash/ExtraTools/__init__.py` eagerly imports all 7 submodules. Importing `lash.ExtraTools.app_random` via `importlib` will trigger this file first, loading ALL ExtraTools. Must be emptied.

**Critical:** `lash/__init__.py` calls `Global()` at line 37 unconditionally. Importing any `lash.*` submodule triggers the package init and re-enters the CLI. Must move `Global()` to `__main__.py` only.

---

## Design Decisions

### No intermediate static `_COMMANDS` state

The original plan had Phase 1 create a hard-coded `_COMMANDS` dict in `__init__.py`. This is skipped. It would show all 15 commands in `--help` even before deps are installed, causing `ImportError` on invocation. `__init__.py` goes straight to plugin-based loading.

### Core plugins (auto-included, zero deps)

`random` and `crack` have no pip dependencies. Their manifests carry `"core": true`. `get_lazy_commands()` always includes core plugin commands regardless of `installed.json`. Users see them immediately after install with no `lash download` required.

### Per-command dependency tracking

Manifests declare `requires` per command, not per plugin. This enables:
- Installing `organize` without `zip` (saves pyminizip install)
- Removing `organize` and only uninstalling `rich` if `zip` is also removed (shared dep preserved)

### Command-centric state file

`~/.lash/installed.json` tracks commands, not plugins:

```json
{
  "installed_commands": {
    "organize": {
      "plugin": "file_tools",
      "requires": ["rich>=12.6.0"]
    },
    "zip": {
      "plugin": "file_tools",
      "requires": ["pyminizip>=0.2.6", "rich>=12.6.0"]
    },
    "autoclick": {
      "plugin": "device_tools",
      "requires": ["pynput>=1.7.6"]
    }
  }
}
```

Orphaned dep check on removal: `cmd_requires - union(requires of all remaining commands)`.

### Manifest format

```json
{
  "name": "file_tools",
  "description": "File organization and ZIP tools",
  "commands": {
    "organize": {
      "module": "lash.file_handler:organize",
      "description": "Organize files by type",
      "requires": ["rich>=12.6.0"]
    },
    "zip": {
      "module": "lash.file_handler:zip_group",
      "description": "ZIP compression and extraction",
      "requires": ["pyminizip>=0.2.6", "rich>=12.6.0"]
    }
  }
}
```

---

## File Structure

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `lash/core/__init__.py` | Package marker (empty) |
| Create | `lash/core/lazy_group.py` | `LazyGroup` class |
| Create | `lash/core/downloader.py` | `lash download` command |
| Create | `lash/core/remover.py` | `lash remove` command + dep cleanup |
| Create | `lash/core/plugin_list.py` | `lash plugins` list command |
| Create | `lash/plugins/__init__.py` | Plugin discovery + state management |
| Create | `lash/plugins/file_tools/manifest.json` | organize + zip commands |
| Create | `lash/plugins/image_tools/manifest.json` | image commands |
| Create | `lash/plugins/video_tools/manifest.json` | video commands |
| Create | `lash/plugins/audio_tools/manifest.json` | audio commands |
| Create | `lash/plugins/web_tools/manifest.json` | web commands |
| Create | `lash/plugins/spy_tools/manifest.json` | spy commands |
| Create | `lash/plugins/calc_tools/manifest.json` | calc commands |
| Create | `lash/plugins/monitor_tools/manifest.json` | monitor command |
| Create | `lash/plugins/work_tools/manifest.json` | work command |
| Create | `lash/plugins/sched_tools/manifest.json` | sched commands |
| Create | `lash/plugins/device_tools/manifest.json` | autoclick + keyhold |
| Create | `lash/plugins/crack_tools/manifest.json` | crack (core, zero deps) |
| Create | `lash/plugins/random_tools/manifest.json` | random (core, zero deps) |
| Create | `tests/__init__.py` | Test package marker (empty) |
| Create | `tests/test_lazy_group.py` | Unit tests for LazyGroup |
| Create | `tests/test_plugin_registry.py` | Unit tests for plugin discovery |
| Create | `tests/test_downloader.py` | Unit tests for download command |
| Create | `tests/test_remover.py` | Unit tests for remove + dep cleanup |
| Create | `tests/test_plugin_list.py` | Unit tests for plugins list command |
| Modify | `lash/ExtraTools/__init__.py` | Empty (remove all eager imports) |
| Modify | `lash/__init__.py` | LazyGroup + core commands, no Global() call |
| Modify | `lash/__main__.py` | Call Global() here only |
| Modify | `setup.py` | install_requires: click only; add extras_require[all] |

---

## Task 1: LazyGroup class

**Files:**
- Create: `lash/core/__init__.py`
- Create: `lash/core/lazy_group.py`
- Create: `tests/__init__.py`
- Create: `tests/test_lazy_group.py`

- [ ] **Step 1: Write failing tests**

Create `tests/__init__.py` — empty file.

Create `tests/test_lazy_group.py`:

```python
from unittest import mock
import click
from click.testing import CliRunner


class TestLazyGroupListCommands:
    def test_returns_lazy_names_without_importing(self):
        from lash.core.lazy_group import LazyGroup
        group = LazyGroup(name='test', lazy_subcommands={'foo': 'nonexistent_xyz:attr'})
        ctx = click.Context(group)
        # nonexistent module — proves import is never triggered
        result = group.list_commands(ctx)
        assert 'foo' in result

    def test_merges_lazy_and_eager_commands(self):
        from lash.core.lazy_group import LazyGroup
        group = LazyGroup(name='test', lazy_subcommands={'lazy_cmd': 'os:getcwd'})

        @group.command('eager_cmd')
        def eager():
            pass

        ctx = click.Context(group)
        result = group.list_commands(ctx)
        assert 'lazy_cmd' in result
        assert 'eager_cmd' in result

    def test_result_is_sorted(self):
        from lash.core.lazy_group import LazyGroup
        group = LazyGroup(name='test', lazy_subcommands={'zzz': 'os:getcwd', 'aaa': 'os:getcwd'})
        ctx = click.Context(group)
        result = group.list_commands(ctx)
        assert result == sorted(result)

    def test_help_does_not_import_lazy_modules(self):
        from lash.core.lazy_group import LazyGroup
        group = LazyGroup(name='root', lazy_subcommands={'video': 'nonexistent_heavy:video'})
        runner = CliRunner()
        with mock.patch('importlib.import_module') as mock_import:
            result = runner.invoke(group, ['--help'])
            mock_import.assert_not_called()
        assert 'video' in result.output


class TestLazyGroupGetCommand:
    def test_imports_module_and_returns_attr(self):
        from lash.core.lazy_group import LazyGroup

        @click.command('mycommand')
        def mycommand():
            pass

        fake_module = mock.MagicMock()
        fake_module.mycommand = mycommand

        with mock.patch('importlib.import_module', return_value=fake_module) as mock_import:
            group = LazyGroup(name='test', lazy_subcommands={'mycommand': 'fake.module:mycommand'})
            ctx = click.Context(group)
            result = group.get_command(ctx, 'mycommand')

        mock_import.assert_called_once_with('fake.module')
        assert result is mycommand

    def test_returns_none_for_unknown_command(self):
        from lash.core.lazy_group import LazyGroup
        group = LazyGroup(name='test', lazy_subcommands={'foo': 'os:getcwd'})
        ctx = click.Context(group)
        assert group.get_command(ctx, 'does_not_exist') is None

    def test_lazy_command_invocable_end_to_end(self):
        from lash.core.lazy_group import LazyGroup

        @click.command('greet')
        def greet():
            click.echo('hello from lazy')

        fake_module = mock.MagicMock()
        fake_module.greet = greet

        with mock.patch('importlib.import_module', return_value=fake_module):
            group = LazyGroup(name='root', lazy_subcommands={'greet': 'fake.module:greet'})
            runner = CliRunner()
            result = runner.invoke(group, ['greet'])

        assert result.exit_code == 0
        assert 'hello from lazy' in result.output
```

- [ ] **Step 2: Run tests, verify they fail**

```
pytest tests/test_lazy_group.py -v
```

Expected: `ModuleNotFoundError: No module named 'lash.core.lazy_group'`

- [ ] **Step 3: Create package markers**

Create `lash/core/__init__.py` — empty file.

- [ ] **Step 4: Write LazyGroup implementation**

Create `lash/core/lazy_group.py`:

```python
import importlib
import click


class LazyGroup(click.Group):
    def __init__(self, *args, lazy_subcommands=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._lazy = lazy_subcommands or {}

    def list_commands(self, ctx):
        eager = set(super().list_commands(ctx))
        return sorted(eager | set(self._lazy.keys()))

    def get_command(self, ctx, cmd_name):
        if cmd_name in self._lazy:
            module_path, attr = self._lazy[cmd_name].rsplit(':', 1)
            module = importlib.import_module(module_path)
            return getattr(module, attr)
        return super().get_command(ctx, cmd_name)
```

- [ ] **Step 5: Run tests, verify they pass**

```
pytest tests/test_lazy_group.py -v
```

Expected: 7 tests PASS

- [ ] **Step 6: Commit**

```bash
git add lash/core/__init__.py lash/core/lazy_group.py tests/__init__.py tests/test_lazy_group.py
git commit -m "feat: add LazyGroup for deferred Click command imports"
```

---

## Task 2: Empty ExtraTools/__init__.py

**Context:** `lash/ExtraTools/__init__.py` currently imports all 7 submodules. Any `importlib.import_module('lash.ExtraTools.app_random')` call triggers this file first, loading all ExtraTools. Must be emptied.

**Files:**
- Modify: `lash/ExtraTools/__init__.py`
- Possibly modify: `lash/Exportables/__init__.py`

- [ ] **Step 1: Read both files**

Read `lash/ExtraTools/__init__.py` — confirm it contains:
```python
from .Devices import *
from .sched_manager import *
from .monitor import *
from .work import *
from .app_random import *
from .app_math import *
from .brute_force import *
```

Read `lash/Exportables/__init__.py` — if it contains wildcard submodule imports, it needs the same treatment.

- [ ] **Step 2: Check no handler imports from ExtraTools package root**

```
grep -r "from lash.ExtraTools import" lash/
grep -r "from lash.Exportables import" lash/
```

Expected: zero results. All handlers import from specific submodules (`from lash.Exportables.fileTools import *`), not from package roots. If any results appear, note them — those callers need updating before the package inits are emptied.

- [ ] **Step 3: Empty ExtraTools/__init__.py**

Replace entire content with empty file (no imports, no comments).

- [ ] **Step 4: Empty Exportables/__init__.py if needed**

Apply same treatment if Step 1 found wildcard submodule imports there.

- [ ] **Step 5: Commit**

```bash
git add lash/ExtraTools/__init__.py
git commit -m "fix: remove eager submodule imports from ExtraTools package init"
```

---

## Task 3: Plugin manifests

**Context:** Per-command manifest format. Each command declares its own `module` path and `requires` list. Plugins with `"core": true` are auto-included in `--help` without installation. The `lash/plugins/__init__.py` created here is an empty placeholder; real logic comes in Task 4.

**Files:**
- Create: `lash/plugins/__init__.py`
- Create: all 13 `manifest.json` files

- [ ] **Step 1: Create `lash/plugins/__init__.py`**

Empty file — package marker only.

- [ ] **Step 2: Create `lash/plugins/random_tools/manifest.json`**

```json
{
  "name": "random_tools",
  "description": "Random sequence generator",
  "core": true,
  "commands": {
    "random": {
      "module": "lash.ExtraTools.app_random:random",
      "description": "Generate random sequences",
      "requires": []
    }
  }
}
```

- [ ] **Step 3: Create `lash/plugins/crack_tools/manifest.json`**

```json
{
  "name": "crack_tools",
  "description": "ZIP password cracker via brute force",
  "core": true,
  "commands": {
    "crack": {
      "module": "lash.ExtraTools.brute_force:crack",
      "description": "Brute-force crack encrypted ZIP files",
      "requires": []
    }
  }
}
```

- [ ] **Step 4: Create `lash/plugins/file_tools/manifest.json`**

```json
{
  "name": "file_tools",
  "description": "File organization and ZIP compression tools",
  "commands": {
    "organize": {
      "module": "lash.file_handler:organize",
      "description": "Organize files in a directory by type",
      "requires": ["rich>=12.6.0"]
    },
    "zip": {
      "module": "lash.file_handler:zip_group",
      "description": "ZIP compression, extraction, encoding",
      "requires": ["pyminizip>=0.2.6", "rich>=12.6.0"]
    }
  }
}
```

- [ ] **Step 5: Create `lash/plugins/image_tools/manifest.json`**

```json
{
  "name": "image_tools",
  "description": "Image editing, filtering, and watermarking tools",
  "commands": {
    "image": {
      "module": "lash.image_handler:image",
      "description": "Flip, resize, adjust, filter, watermark images",
      "requires": ["Pillow>=9.3.0", "tqdm>=4.64.1"]
    }
  }
}
```

- [ ] **Step 6: Create `lash/plugins/video_tools/manifest.json`**

```json
{
  "name": "video_tools",
  "description": "Video recording, editing, and building tools",
  "commands": {
    "video": {
      "module": "lash.video_handler:video",
      "description": "Record, edit, build, and cut video files",
      "requires": [
        "opencv-python>=4.6.0.66",
        "numpy>=1.23.4",
        "mss>=7.0.1",
        "moviepy>=1.0.3",
        "pyautogui>=0.9.53",
        "keyboard>=0.13.5",
        "tqdm>=4.64.1"
      ]
    }
  }
}
```

- [ ] **Step 7: Create `lash/plugins/audio_tools/manifest.json`**

```json
{
  "name": "audio_tools",
  "description": "Audio extraction and cutting tools",
  "commands": {
    "audio": {
      "module": "lash.audio_handler:audio_group",
      "description": "Extract and cut audio from video files",
      "requires": ["moviepy>=1.0.3"]
    }
  }
}
```

- [ ] **Step 8: Create `lash/plugins/web_tools/manifest.json`**

```json
{
  "name": "web_tools",
  "description": "Web scraping, Wikipedia, YouTube, news, and email tools",
  "commands": {
    "web": {
      "module": "lash.web_scraping:web",
      "description": "Scrape GitHub, Wikipedia, YouTube, news; send mail",
      "requires": [
        "bs4>=0.0.1",
        "requests>=2.28.0",
        "wikipedia>=1.4.0",
        "pytube>=12.1.0",
        "gnews>=0.2.7",
        "rich>=12.6.0",
        "quick-mailer>=2022.2.22"
      ]
    }
  }
}
```

- [ ] **Step 9: Create `lash/plugins/spy_tools/manifest.json`**

```json
{
  "name": "spy_tools",
  "description": "Keylogger, AES encryption, and injection tools",
  "commands": {
    "spy": {
      "module": "lash.spy:spy",
      "description": "Keylogger, AES crypt, keyboard injection",
      "requires": ["pyaes>=1.6.1", "pynput>=1.7.6"]
    }
  }
}
```

- [ ] **Step 10: Create `lash/plugins/calc_tools/manifest.json`**

```json
{
  "name": "calc_tools",
  "description": "Math calculator: probability, cartesian, binomial, trinomial",
  "commands": {
    "calc": {
      "module": "lash.ExtraTools.app_math:calc",
      "description": "Probability, cartesian product, binomial, trinomial",
      "requires": ["numpy>=1.23.4", "matplotlib>=3.6.1"]
    }
  }
}
```

- [ ] **Step 11: Create `lash/plugins/monitor_tools/manifest.json`**

```json
{
  "name": "monitor_tools",
  "description": "System performance dashboard",
  "commands": {
    "monitor": {
      "module": "lash.ExtraTools.monitor:monitor",
      "description": "Live CPU, RAM, disk, and network dashboard",
      "requires": ["psutil>=5.9.3", "py-dashing>=0.3.dev0"]
    }
  }
}
```

- [ ] **Step 12: Create `lash/plugins/work_tools/manifest.json`**

```json
{
  "name": "work_tools",
  "description": "Work session time tracking and reporting",
  "commands": {
    "work": {
      "module": "lash.ExtraTools.work:work",
      "description": "Track and report work session times",
      "requires": ["pandas>=1.5.1", "matplotlib>=3.6.1"]
    }
  }
}
```

- [ ] **Step 13: Create `lash/plugins/sched_tools/manifest.json`**

```json
{
  "name": "sched_tools",
  "description": "Task scheduling: run, wait, exec",
  "commands": {
    "sched": {
      "module": "lash.ExtraTools.sched_manager:sched",
      "description": "Schedule and wait on recurring tasks",
      "requires": ["schedule>=1.1.0"]
    }
  }
}
```

- [ ] **Step 14: Create `lash/plugins/device_tools/manifest.json`**

```json
{
  "name": "device_tools",
  "description": "Keyboard hold and mouse auto-click automation",
  "commands": {
    "autoclick": {
      "module": "lash.ExtraTools.Devices.tmouse:autoclick",
      "description": "Automate mouse clicks at intervals",
      "requires": ["pynput>=1.7.6"]
    },
    "keyhold": {
      "module": "lash.ExtraTools.Devices.keyboard:keyhold",
      "description": "Hold a keyboard key for a duration",
      "requires": ["pynput>=1.7.6"]
    }
  }
}
```

- [ ] **Step 15: Commit**

```bash
git add lash/plugins/
git commit -m "feat: add per-command plugin manifests for all lash tools"
```

---

## Task 4: Plugin registry module

**Files:**
- Modify: `lash/plugins/__init__.py`
- Create: `tests/test_plugin_registry.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_plugin_registry.py`:

```python
import json
import pathlib
import pytest


def _make_manifest(tmp_path, name, commands, core=False):
    plugin_dir = tmp_path / name
    plugin_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": name,
        "description": f"Test plugin {name}",
        "commands": commands,
    }
    if core:
        manifest["core"] = True
    (plugin_dir / 'manifest.json').write_text(json.dumps(manifest))
    return plugin_dir


def _cmd(module, requires=None):
    return {"module": module, "description": "test", "requires": requires or []}


class TestGetAvailablePlugins:
    def test_reads_all_manifests(self, tmp_path):
        from lash.plugins import get_available_plugins
        _make_manifest(tmp_path, 'web_tools', {'web': _cmd('lash.web_scraping:web')})
        _make_manifest(tmp_path, 'image_tools', {'image': _cmd('lash.image_handler:image')})
        result = get_available_plugins(plugins_dir=tmp_path)
        assert 'web_tools' in result
        assert 'image_tools' in result

    def test_ignores_dirs_without_manifest(self, tmp_path):
        from lash.plugins import get_available_plugins
        (tmp_path / 'orphan_dir').mkdir()
        result = get_available_plugins(plugins_dir=tmp_path)
        assert 'orphan_dir' not in result

    def test_command_data_accessible(self, tmp_path):
        from lash.plugins import get_available_plugins
        _make_manifest(tmp_path, 'file_tools', {
            'organize': _cmd('lash.file_handler:organize', ['rich>=12.6.0']),
            'zip': _cmd('lash.file_handler:zip_group', ['pyminizip>=0.2.6', 'rich>=12.6.0']),
        })
        result = get_available_plugins(plugins_dir=tmp_path)
        assert result['file_tools']['commands']['organize']['module'] == 'lash.file_handler:organize'
        assert 'rich>=12.6.0' in result['file_tools']['commands']['organize']['requires']


class TestGetLazyCommands:
    def test_core_commands_always_included(self, tmp_path):
        from lash.plugins import get_lazy_commands
        _make_manifest(tmp_path, 'random_tools', {'random': _cmd('lash.ExtraTools.app_random:random')}, core=True)
        state_file = tmp_path / 'installed.json'  # does not exist
        result = get_lazy_commands(plugins_dir=tmp_path, state_file=state_file)
        assert 'random' in result
        assert result['random'] == 'lash.ExtraTools.app_random:random'

    def test_installed_commands_included(self, tmp_path):
        from lash.plugins import get_lazy_commands
        _make_manifest(tmp_path, 'web_tools', {'web': _cmd('lash.web_scraping:web')})
        state_file = tmp_path / 'installed.json'
        state_file.write_text(json.dumps({
            'installed_commands': {
                'web': {'plugin': 'web_tools', 'requires': ['bs4>=0.0.1']}
            }
        }))
        result = get_lazy_commands(plugins_dir=tmp_path, state_file=state_file)
        assert 'web' in result

    def test_uninstalled_commands_excluded(self, tmp_path):
        from lash.plugins import get_lazy_commands
        _make_manifest(tmp_path, 'web_tools', {'web': _cmd('lash.web_scraping:web')})
        state_file = tmp_path / 'installed.json'  # does not exist
        result = get_lazy_commands(plugins_dir=tmp_path, state_file=state_file)
        assert 'web' not in result


class TestMarkCommandInstalled:
    def test_creates_state_file_if_missing(self, tmp_path):
        from lash.plugins import mark_command_installed
        state_file = tmp_path / 'installed.json'
        mark_command_installed('web', 'web_tools', ['bs4>=0.0.1'], state_file=state_file)
        assert state_file.exists()
        state = json.loads(state_file.read_text())
        assert 'web' in state['installed_commands']

    def test_preserves_existing_commands(self, tmp_path):
        from lash.plugins import mark_command_installed
        state_file = tmp_path / 'installed.json'
        state_file.write_text(json.dumps({
            'installed_commands': {'organize': {'plugin': 'file_tools', 'requires': []}}
        }))
        mark_command_installed('zip', 'file_tools', ['pyminizip>=0.2.6'], state_file=state_file)
        state = json.loads(state_file.read_text())
        assert 'organize' in state['installed_commands']
        assert 'zip' in state['installed_commands']


class TestRemoveCommand:
    def test_returns_orphaned_deps(self, tmp_path):
        from lash.plugins import remove_command
        state_file = tmp_path / 'installed.json'
        state_file.write_text(json.dumps({
            'installed_commands': {
                'organize': {'plugin': 'file_tools', 'requires': ['rich>=12.6.0']},
                'zip': {'plugin': 'file_tools', 'requires': ['pyminizip>=0.2.6', 'rich>=12.6.0']},
            }
        }))
        orphaned = remove_command('organize', state_file=state_file)
        # rich is still needed by zip, so only nothing is orphaned
        assert 'rich>=12.6.0' not in orphaned
        state = json.loads(state_file.read_text())
        assert 'organize' not in state['installed_commands']

    def test_returns_truly_orphaned_deps(self, tmp_path):
        from lash.plugins import remove_command
        state_file = tmp_path / 'installed.json'
        state_file.write_text(json.dumps({
            'installed_commands': {
                'organize': {'plugin': 'file_tools', 'requires': ['rich>=12.6.0']},
            }
        }))
        orphaned = remove_command('organize', state_file=state_file)
        assert 'rich>=12.6.0' in orphaned

    def test_returns_empty_for_unknown_command(self, tmp_path):
        from lash.plugins import remove_command
        state_file = tmp_path / 'installed.json'
        state_file.write_text(json.dumps({'installed_commands': {}}))
        orphaned = remove_command('nonexistent', state_file=state_file)
        assert orphaned == []

    def test_removes_command_from_state(self, tmp_path):
        from lash.plugins import remove_command
        state_file = tmp_path / 'installed.json'
        state_file.write_text(json.dumps({
            'installed_commands': {
                'web': {'plugin': 'web_tools', 'requires': ['bs4>=0.0.1']}
            }
        }))
        remove_command('web', state_file=state_file)
        state = json.loads(state_file.read_text())
        assert 'web' not in state['installed_commands']
```

- [ ] **Step 2: Run tests, verify they fail**

```
pytest tests/test_plugin_registry.py -v
```

Expected: `ImportError: cannot import name 'get_available_plugins' from 'lash.plugins'`

- [ ] **Step 3: Write plugin registry implementation**

Replace `lash/plugins/__init__.py` with:

```python
import json
import pathlib

_DEFAULT_PLUGINS_DIR = pathlib.Path(__file__).parent
_DEFAULT_STATE_FILE = pathlib.Path.home() / '.lash' / 'installed.json'


def _load_state(state_file):
    state_file = state_file or _DEFAULT_STATE_FILE
    if not pathlib.Path(state_file).exists():
        return {'installed_commands': {}}
    try:
        return json.loads(pathlib.Path(state_file).read_text())
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
```

- [ ] **Step 4: Run tests, verify they pass**

```
pytest tests/test_plugin_registry.py -v
```

Expected: all 13 tests PASS

- [ ] **Step 5: Commit**

```bash
git add lash/plugins/__init__.py tests/test_plugin_registry.py
git commit -m "feat: add plugin registry with command-level state and orphan dep detection"
```

---

## Task 5: `lash download` command

**Files:**
- Create: `lash/core/downloader.py`
- Create: `tests/test_downloader.py`

### CLI interface

```
lash download <plugin>                    # install all commands in plugin
lash download <plugin> --only cmd1 cmd2  # install only selected commands
```

Examples:
```
lash download file_tools                  # installs organize + zip
lash download file_tools --only organize  # installs organize only (no pyminizip)
lash download device_tools --only keyhold # installs keyhold only
```

- [ ] **Step 1: Write failing tests**

Create `tests/test_downloader.py`:

```python
import json
import pathlib
import pytest
from unittest import mock
from click.testing import CliRunner


def _setup_plugins(tmp_path):
    for name, commands in [
        ('crack_tools', {'crack': {'module': 'lash.ExtraTools.brute_force:crack', 'description': 'd', 'requires': []}}),
        ('file_tools', {
            'organize': {'module': 'lash.file_handler:organize', 'description': 'd', 'requires': ['rich>=12.6.0']},
            'zip': {'module': 'lash.file_handler:zip_group', 'description': 'd', 'requires': ['pyminizip>=0.2.6', 'rich>=12.6.0']},
        }),
        ('device_tools', {
            'autoclick': {'module': 'lash.ExtraTools.Devices.tmouse:autoclick', 'description': 'd', 'requires': ['pynput>=1.7.6']},
            'keyhold': {'module': 'lash.ExtraTools.Devices.keyboard:keyhold', 'description': 'd', 'requires': ['pynput>=1.7.6']},
        }),
    ]:
        d = tmp_path / name
        d.mkdir()
        (d / 'manifest.json').write_text(json.dumps({'name': name, 'description': 'd', 'commands': commands}))
    return tmp_path


def _invoke(tool, args, plugins_dir, state_file, pip_returncode=0):
    from lash.core.downloader import make_download_command
    cmd = make_download_command(plugins_dir=plugins_dir, state_file=state_file)
    runner = CliRunner()
    with mock.patch('subprocess.run') as mock_run:
        mock_run.return_value = mock.MagicMock(returncode=pip_returncode, stderr='')
        result = runner.invoke(cmd, [tool] + args)
    return result, mock_run


class TestDownloadAll:
    def test_installs_all_commands_of_plugin(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        result, _ = _invoke('file_tools', [], plugins_dir, state_file)
        assert result.exit_code == 0
        state = json.loads(state_file.read_text())
        assert 'organize' in state['installed_commands']
        assert 'zip' in state['installed_commands']

    def test_no_pip_call_when_zero_deps(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        result, mock_run = _invoke('crack_tools', [], plugins_dir, state_file)
        assert result.exit_code == 0
        mock_run.assert_not_called()

    def test_pip_called_with_deduplicated_requires(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        result, mock_run = _invoke('file_tools', [], plugins_dir, state_file)
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        # rich appears in both commands but pip should receive it once
        assert call_args.count('rich>=12.6.0') == 1

    def test_skips_already_installed_commands(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        state_file.write_text(json.dumps({
            'installed_commands': {
                'organize': {'plugin': 'file_tools', 'requires': ['rich>=12.6.0']}
            }
        }))
        result, mock_run = _invoke('file_tools', [], plugins_dir, state_file)
        assert result.exit_code == 0
        # only zip is new, pip only called for pyminizip (rich already installed)
        state = json.loads(state_file.read_text())
        assert 'zip' in state['installed_commands']


class TestDownloadOnly:
    def test_installs_only_selected_commands(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        result, mock_run = _invoke('file_tools', ['--only', 'organize'], plugins_dir, state_file)
        assert result.exit_code == 0
        state = json.loads(state_file.read_text())
        assert 'organize' in state['installed_commands']
        assert 'zip' not in state['installed_commands']

    def test_only_installs_deps_of_selected_commands(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        result, mock_run = _invoke('file_tools', ['--only', 'organize'], plugins_dir, state_file)
        call_args = mock_run.call_args[0][0]
        assert 'pyminizip>=0.2.6' not in call_args  # zip's dep, not installed

    def test_only_with_multiple_commands(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        result, _ = _invoke('device_tools', ['--only', 'autoclick', 'keyhold'], plugins_dir, state_file)
        assert result.exit_code == 0
        state = json.loads(state_file.read_text())
        assert 'autoclick' in state['installed_commands']
        assert 'keyhold' in state['installed_commands']

    def test_unknown_command_in_only_fails(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        result, _ = _invoke('file_tools', ['--only', 'bogus_cmd'], plugins_dir, state_file)
        assert result.exit_code != 0
        assert 'bogus_cmd' in result.output


class TestDownloadErrors:
    def test_unknown_plugin_fails(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        result, _ = _invoke('nonexistent_plugin', [], plugins_dir, state_file)
        assert result.exit_code != 0
        assert 'Unknown plugin' in result.output

    def test_lists_available_plugins_on_unknown(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        result, _ = _invoke('bogus', [], plugins_dir, state_file)
        assert 'file_tools' in result.output or 'crack_tools' in result.output

    def test_pip_failure_aborts_and_does_not_mark_installed(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        result, _ = _invoke('file_tools', [], plugins_dir, state_file, pip_returncode=1)
        assert result.exit_code != 0
        assert not state_file.exists() or 'organize' not in json.loads(state_file.read_text()).get('installed_commands', {})
```

- [ ] **Step 2: Run tests, verify they fail**

```
pytest tests/test_downloader.py -v
```

Expected: `ImportError: cannot import name 'make_download_command'`

- [ ] **Step 3: Write download command implementation**

Create `lash/core/downloader.py`:

```python
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

        # Collect deduplicated requires for commands not yet installed
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
```

- [ ] **Step 4: Run tests, verify they pass**

```
pytest tests/test_downloader.py -v
```

Expected: all 11 tests PASS

- [ ] **Step 5: Commit**

```bash
git add lash/core/downloader.py tests/test_downloader.py
git commit -m "feat: add lash download with --only flag for granular command installation"
```

---

## Task 6: `lash remove` command

**Files:**
- Create: `lash/core/remover.py`
- Create: `tests/test_remover.py`

### CLI interface

```
lash remove <plugin>               # remove all installed commands of plugin + cleanup deps
lash remove <plugin> --cmd cmd1   # remove only cmd1 from plugin + cleanup deps
```

Examples:
```
lash remove file_tools             # removes organize + zip, uninstalls pyminizip (if orphaned)
lash remove file_tools --cmd zip   # removes zip only; rich kept if organize still installed
```

- [ ] **Step 1: Write failing tests**

Create `tests/test_remover.py`:

```python
import json
import pathlib
import pytest
from unittest import mock
from click.testing import CliRunner


def _setup_state(state_file, installed_commands):
    pathlib.Path(state_file).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(state_file).write_text(json.dumps({'installed_commands': installed_commands}))


def _setup_plugins(tmp_path):
    for name, commands in [
        ('file_tools', {
            'organize': {'module': 'lash.file_handler:organize', 'description': 'd', 'requires': ['rich>=12.6.0']},
            'zip': {'module': 'lash.file_handler:zip_group', 'description': 'd', 'requires': ['pyminizip>=0.2.6', 'rich>=12.6.0']},
        }),
        ('web_tools', {
            'web': {'module': 'lash.web_scraping:web', 'description': 'd', 'requires': ['bs4>=0.0.1', 'rich>=12.6.0']},
        }),
    ]:
        d = tmp_path / name
        d.mkdir()
        (d / 'manifest.json').write_text(json.dumps({'name': name, 'description': 'd', 'commands': commands}))
    return tmp_path


def _invoke(plugin, args, plugins_dir, state_file, pip_returncode=0):
    from lash.core.remover import make_remove_command
    cmd = make_remove_command(plugins_dir=plugins_dir, state_file=state_file)
    runner = CliRunner()
    with mock.patch('subprocess.run') as mock_run:
        mock_run.return_value = mock.MagicMock(returncode=pip_returncode, stderr='')
        result = runner.invoke(cmd, [plugin] + args)
    return result, mock_run


class TestRemoveAll:
    def test_removes_all_commands_of_plugin(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        _setup_state(state_file, {
            'organize': {'plugin': 'file_tools', 'requires': ['rich>=12.6.0']},
            'zip': {'plugin': 'file_tools', 'requires': ['pyminizip>=0.2.6', 'rich>=12.6.0']},
        })
        result, _ = _invoke('file_tools', [], plugins_dir, state_file)
        assert result.exit_code == 0
        state = json.loads(state_file.read_text())
        assert 'organize' not in state['installed_commands']
        assert 'zip' not in state['installed_commands']

    def test_uninstalls_orphaned_deps(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        _setup_state(state_file, {
            'organize': {'plugin': 'file_tools', 'requires': ['rich>=12.6.0']},
            'zip': {'plugin': 'file_tools', 'requires': ['pyminizip>=0.2.6', 'rich>=12.6.0']},
        })
        result, mock_run = _invoke('file_tools', [], plugins_dir, state_file)
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        # both commands removed → rich and pyminizip both orphaned
        assert 'rich' in ' '.join(call_args)
        assert 'pyminizip' in ' '.join(call_args)

    def test_preserves_deps_used_by_other_plugins(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        _setup_state(state_file, {
            'organize': {'plugin': 'file_tools', 'requires': ['rich>=12.6.0']},
            'web': {'plugin': 'web_tools', 'requires': ['bs4>=0.0.1', 'rich>=12.6.0']},
        })
        result, mock_run = _invoke('file_tools', [], plugins_dir, state_file)
        assert result.exit_code == 0
        if mock_run.called:
            call_args = mock_run.call_args[0][0]
            # rich still needed by web → must NOT be uninstalled
            assert 'rich' not in call_args

    def test_nothing_to_remove_exits_cleanly(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        _setup_state(state_file, {})
        result, _ = _invoke('file_tools', [], plugins_dir, state_file)
        assert result.exit_code == 0
        assert 'nothing' in result.output.lower() or 'not installed' in result.output.lower()


class TestRemoveCmd:
    def test_removes_single_command(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        _setup_state(state_file, {
            'organize': {'plugin': 'file_tools', 'requires': ['rich>=12.6.0']},
            'zip': {'plugin': 'file_tools', 'requires': ['pyminizip>=0.2.6', 'rich>=12.6.0']},
        })
        result, mock_run = _invoke('file_tools', ['--cmd', 'zip'], plugins_dir, state_file)
        assert result.exit_code == 0
        state = json.loads(state_file.read_text())
        assert 'zip' not in state['installed_commands']
        assert 'organize' in state['installed_commands']  # untouched

    def test_keeps_shared_dep_when_sibling_command_remains(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        _setup_state(state_file, {
            'organize': {'plugin': 'file_tools', 'requires': ['rich>=12.6.0']},
            'zip': {'plugin': 'file_tools', 'requires': ['pyminizip>=0.2.6', 'rich>=12.6.0']},
        })
        result, mock_run = _invoke('file_tools', ['--cmd', 'zip'], plugins_dir, state_file)
        if mock_run.called:
            call_args = mock_run.call_args[0][0]
            assert 'rich' not in call_args  # rich still needed by organize
            assert 'pyminizip' in call_args  # pyminizip orphaned

    def test_unknown_cmd_flag_fails(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        _setup_state(state_file, {'organize': {'plugin': 'file_tools', 'requires': []}})
        result, _ = _invoke('file_tools', ['--cmd', 'bogus_cmd'], plugins_dir, state_file)
        assert result.exit_code != 0


class TestRemoveErrors:
    def test_unknown_plugin_fails(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        _setup_state(state_file, {})
        result, _ = _invoke('nonexistent_plugin', [], plugins_dir, state_file)
        assert result.exit_code != 0
        assert 'Unknown plugin' in result.output
```

- [ ] **Step 2: Run tests, verify they fail**

```
pytest tests/test_remover.py -v
```

Expected: `ImportError: cannot import name 'make_remove_command'`

- [ ] **Step 3: Write remove command implementation**

Create `lash/core/remover.py`:

```python
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

        # Determine which commands of this plugin are currently installed
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

        # Remove commands one by one, collecting all orphaned deps
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
```

- [ ] **Step 4: Run tests, verify they pass**

```
pytest tests/test_remover.py -v
```

Expected: all 11 tests PASS

- [ ] **Step 5: Commit**

```bash
git add lash/core/remover.py tests/test_remover.py
git commit -m "feat: add lash remove with orphaned dependency cleanup"
```

---

## Task 7: `lash plugins` list command

**Files:**
- Create: `lash/core/plugin_list.py`
- Create: `tests/test_plugin_list.py`

### CLI interface

```
lash plugins               # show installed commands grouped by plugin
lash plugins --available   # also show available (not installed) plugins
```

Example output:
```
Installed:
  file_tools
    ✓ organize   Organize files by type
    ✓ zip        ZIP compression and extraction

  device_tools
    ✓ autoclick  Automate mouse clicks at intervals

Core (always available):
  random_tools
    ● random     Generate random sequences
  crack_tools
    ● crack      Brute-force crack encrypted ZIP files

Run 'lash download <plugin> --help' to see install options.
```

With `--available`:
```
Not installed:
  image_tools      Image editing, filtering, and watermarking tools
  video_tools      Video recording, editing, and building tools
  ...
```

- [ ] **Step 1: Write failing tests**

Create `tests/test_plugin_list.py`:

```python
import json
import pathlib
import pytest
from click.testing import CliRunner


def _setup(tmp_path):
    for name, core, commands in [
        ('random_tools', True, {'random': {'module': 'x:y', 'description': 'Generate randoms', 'requires': []}}),
        ('crack_tools', True, {'crack': {'module': 'x:y', 'description': 'Crack zips', 'requires': []}}),
        ('file_tools', False, {
            'organize': {'module': 'x:y', 'description': 'Organize files', 'requires': ['rich>=12.6.0']},
            'zip': {'module': 'x:y', 'description': 'ZIP tools', 'requires': ['pyminizip>=0.2.6']},
        }),
        ('video_tools', False, {'video': {'module': 'x:y', 'description': 'Video tools', 'requires': ['cv2']}}),
    ]:
        d = tmp_path / name
        d.mkdir()
        manifest = {'name': name, 'description': f'{name} desc', 'commands': commands}
        if core:
            manifest['core'] = True
        (d / 'manifest.json').write_text(json.dumps(manifest))
    return tmp_path


def _invoke(args, plugins_dir, state_file):
    from lash.core.plugin_list import make_plugins_command
    cmd = make_plugins_command(plugins_dir=plugins_dir, state_file=state_file)
    runner = CliRunner()
    return runner.invoke(cmd, args)


class TestPluginsList:
    def test_shows_installed_commands(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / 'installed.json'
        state_file.write_text(json.dumps({
            'installed_commands': {
                'organize': {'plugin': 'file_tools', 'requires': ['rich>=12.6.0']},
            }
        }))
        result = _invoke([], plugins_dir, state_file)
        assert result.exit_code == 0
        assert 'organize' in result.output
        assert 'file_tools' in result.output

    def test_shows_core_commands(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / 'installed.json'
        result = _invoke([], plugins_dir, state_file)
        assert result.exit_code == 0
        assert 'random' in result.output
        assert 'crack' in result.output

    def test_hides_uninstalled_non_core_by_default(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / 'installed.json'
        result = _invoke([], plugins_dir, state_file)
        assert 'video_tools' not in result.output
        assert 'video' not in result.output

    def test_available_flag_shows_uninstalled_plugins(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / 'installed.json'
        result = _invoke(['--available'], plugins_dir, state_file)
        assert result.exit_code == 0
        assert 'video_tools' in result.output

    def test_available_flag_does_not_show_fully_installed_plugins(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / 'installed.json'
        state_file.write_text(json.dumps({
            'installed_commands': {
                'organize': {'plugin': 'file_tools', 'requires': []},
                'zip': {'plugin': 'file_tools', 'requires': []},
            }
        }))
        result = _invoke(['--available'], plugins_dir, state_file)
        # file_tools fully installed → should not appear in "not installed" section
        lines_with_file_tools = [l for l in result.output.splitlines() if 'file_tools' in l]
        # It may appear in installed section but NOT in not-installed section
        not_installed_section = result.output.split('Not installed')[-1] if 'Not installed' in result.output else ''
        assert 'file_tools' not in not_installed_section
```

- [ ] **Step 2: Run tests, verify they fail**

```
pytest tests/test_plugin_list.py -v
```

Expected: `ImportError: cannot import name 'make_plugins_command'`

- [ ] **Step 3: Write plugins list implementation**

Create `lash/core/plugin_list.py`:

```python
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

        # Installed (non-core) plugins
        installed_plugin_names = {
            v['plugin'] for v in installed_cmds.values()
        } & set(user_plugins.keys())

        if installed_plugin_names:
            click.echo("Installed:")
            for plugin_name in sorted(installed_plugin_names):
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
                if not any(
                    cmd in installed_cmds
                    for cmd in m['commands'].keys()
                )
            }
            partially_installed = {
                n: m for n, m in user_plugins.items()
                if n not in not_installed and n not in installed_plugin_names
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

        if not installed_plugin_names and not available:
            click.echo("No plugins installed.")
            click.echo("Run 'lash plugins --available' to see what's available.")
            click.echo("Run 'lash download <plugin>' to install.")

    return plugins


plugins = make_plugins_command()
```

- [ ] **Step 4: Run tests, verify they pass**

```
pytest tests/test_plugin_list.py -v
```

Expected: all 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add lash/core/plugin_list.py tests/test_plugin_list.py
git commit -m "feat: add lash plugins command with --available flag"
```

---

## Task 8: Final `lash/__init__.py` + verify `__main__.py`

**Context:** `__init__.py` goes straight to plugin-based loading — no intermediate static `_COMMANDS`. Core commands (`download`, `remove`, `plugins`) are always registered. Lazy user commands come from `plugin_registry.get_lazy_commands()`.

**Files:**
- Modify: `lash/__init__.py`
- Modify: `lash/__main__.py`

- [ ] **Step 1: Verify CLI names for `zip_group` and `audio_group`**

Read lines 86-90 of `lash/file_handler.py` to confirm the `name=` in `@click.group(...)`. Read lines 7-10 of `lash/audio_handler.py` for the same.

The `_COMMANDS` dict uses CLI names as keys (what the user types). If `zip_group` is decorated with `@click.group('zip')`, the CLI name is `zip`. Confirm before proceeding.

- [ ] **Step 2: Read `lash/__main__.py`**

Confirm current content. If it already calls `Global()`, we just need to ensure `__init__.py` does NOT.

- [ ] **Step 3: Rewrite `lash/__init__.py`**

```python
import click
from lash.core.lazy_group import LazyGroup
from lash.core.downloader import download
from lash.core.remover import remove
from lash.core.plugin_list import plugins
from lash import plugins as plugin_registry


@click.group(
    name='lash',
    cls=LazyGroup,
    lazy_subcommands=plugin_registry.get_lazy_commands(),
)
def Global():
    """\b
        - Lash 1.2.7 by KevBoyz ~ https://github.com/KevBoyz/Lash
    """


Global.add_command(download)
Global.add_command(remove)
Global.add_command(plugins)
```

**Note:** `get_lazy_commands()` is called once at import time and returns a static dict for this process lifetime. This is correct — a fresh process always reads the current `installed.json`.

- [ ] **Step 4: Update `lash/__main__.py`**

Replace content with:

```python
from lash import Global

if __name__ == '__main__':
    Global()
```

- [ ] **Step 5: Verify no other file calls `Global()` unconditionally**

```
grep -rn "Global()" lash/
```

Expected: zero results (only `__main__.py` calls it, and only inside `if __name__ == '__main__':`).

- [ ] **Step 6: Run all tests**

```
pytest tests/ -v
```

Expected: all tests PASS

- [ ] **Step 7: Commit**

```bash
git add lash/__init__.py lash/__main__.py
git commit -m "feat: finalize CLI entry with plugin-based lazy loading and core commands"
```

---

## Task 9: Slim down `setup.py`

**Files:**
- Modify: `setup.py`

- [ ] **Step 1: Read current `setup.py`**

Confirm the current `install_requires` list of 23 packages.

- [ ] **Step 2: Replace `install_requires`**

Find and replace the `install_requires=[...]` block with:

```python
install_requires=[
    'click>=8.1.3',
],
```

- [ ] **Step 3: Add `extras_require`**

After `install_requires`, add:

```python
extras_require={
    'all': [
        'rich>=12.6.0',
        'pyminizip>=0.2.6',
        'Pillow>=9.3.0',
        'tqdm>=4.64.1',
        'opencv-python>=4.6.0.66',
        'numpy>=1.23.4',
        'mss>=7.0.1',
        'moviepy>=1.0.3',
        'pyautogui>=0.9.53',
        'keyboard>=0.13.5',
        'bs4>=0.0.1',
        'requests>=2.28.0',
        'wikipedia>=1.4.0',
        'pytube>=12.1.0',
        'gnews>=0.2.7',
        'quick-mailer>=2022.2.22',
        'pyaes>=1.6.1',
        'pynput>=1.7.6',
        'matplotlib>=3.6.1',
        'psutil>=5.9.3',
        'py-dashing>=0.3.dev0',
        'pandas>=1.5.1',
        'schedule>=1.1.0',
    ],
},
```

Power users can run `pip install lash[all]` to get everything at once.

- [ ] **Step 4: Run all tests**

```
pytest tests/ -v
```

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add setup.py
git commit -m "chore: slim install_requires to click only; add extras_require[all]"
```

---

## End-to-End Verification Flow

After completing all tasks, verify the full flow manually:

```bash
# Install base (click only)
pip install -e .

# Core commands visible immediately, no heavy imports
lash --help
# Shows: download, remove, plugins, random, crack

# List what's available
lash plugins --available
# Shows all available plugins with descriptions

# Install a plugin fully
lash download file_tools
# Installs rich + pyminizip, enables organize + zip

# Install only one command from a plugin
lash download device_tools --only keyhold
# Installs pynput, enables keyhold only (autoclick not shown in --help)

# Verify installed state
lash plugins
# Shows: file_tools (organize ✓, zip ✓), device_tools (keyhold ✓)

# Add another command later
lash download device_tools --only autoclick
# pynput already installed (shared dep), just marks autoclick as enabled

# Remove a single command
lash remove file_tools --cmd zip
# pyminizip uninstalled (orphaned), rich kept (organize still needs it)

# Remove an entire plugin
lash remove file_tools
# rich uninstalled (now truly orphaned)

# Verify cleanup
lash plugins
# file_tools gone from installed section
```

---

## Risks and Points of Attention

| Risk | Mitigation |
|------|-----------|
| `zip_group` / `audio_group` CLI names differ from Python object names | Task 8 Step 1 reads decorator source to confirm names |
| `ExtraTools/__init__.py` still has eager imports → lazy loading broken for all ExtraTools | Task 2 empties it; Step 2 verifies no callers depend on re-exports |
| `lash/__init__.py` calling `Global()` triggers CLI on any `import lash.*` | Task 8 moves it to `__main__.py` exclusively |
| Dep cleanup uninstalls a package still needed by something outside lash | `pip uninstall` warns if the package is still importable; user sees warning. Cannot fully prevent without a venv audit. |
| `pip uninstall` uses bare package names from requires strings | `_package_name()` strips version specifiers via regex split on `><=!` |
| `get_lazy_commands()` called at import time — plugins installed during the process aren't visible | Expected: new commands visible on next `lash` invocation. Document this. |
| Core plugin commands (random, crack) bypassing `installed.json` could confuse users | `lash plugins` marks them clearly as "Core (always available)" |

### Testing strategy

All tests inject `plugins_dir` and `state_file` parameters — they never touch `~/.lash/`. Run:

```
pytest tests/ -v
```

All 48 tests run without installing the package or touching real plugin state.
