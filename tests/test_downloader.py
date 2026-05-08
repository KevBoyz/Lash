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
        assert call_args.count('rich>=12.6.0') == 1

    def test_skips_already_installed_commands(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        state_file.write_text(json.dumps({
            'installed_commands': {
                'organize': {'plugin': 'file_tools', 'requires': ['rich>=12.6.0']}
            }
        }))
        result, _ = _invoke('file_tools', [], plugins_dir, state_file)
        assert result.exit_code == 0
        state = json.loads(state_file.read_text())
        assert 'zip' in state['installed_commands']


class TestDownloadOnly:
    def test_installs_only_selected_commands(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        result, _ = _invoke('file_tools', ['--only', 'organize'], plugins_dir, state_file)
        assert result.exit_code == 0
        state = json.loads(state_file.read_text())
        assert 'organize' in state['installed_commands']
        assert 'zip' not in state['installed_commands']

    def test_only_installs_deps_of_selected_commands(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / 'installed.json'
        result, mock_run = _invoke('file_tools', ['--only', 'organize'], plugins_dir, state_file)
        call_args = mock_run.call_args[0][0]
        assert 'pyminizip>=0.2.6' not in call_args

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
