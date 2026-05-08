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
        result, _ = _invoke('file_tools', ['--cmd', 'zip'], plugins_dir, state_file)
        assert result.exit_code == 0
        state = json.loads(state_file.read_text())
        assert 'zip' not in state['installed_commands']
        assert 'organize' in state['installed_commands']

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
            assert 'rich' not in call_args
            assert 'pyminizip' in call_args

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
