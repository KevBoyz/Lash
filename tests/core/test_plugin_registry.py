import json


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
        state_file = tmp_path / 'installed.json'
        result = get_lazy_commands(plugins_dir=tmp_path, state_file=state_file)
        assert 'random' in result
        assert result['random']['module'] == 'lash.ExtraTools.app_random:random'

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
        state_file = tmp_path / 'installed.json'
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
