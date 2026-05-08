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
    from lash.core.plugin_list import make_plugin_list_command
    cmd = make_plugin_list_command(plugins_dir=plugins_dir, state_file=state_file)
    runner = CliRunner()
    return runner.invoke(cmd, args)


class TestPluginList:
    def test_default_shows_all_plugins(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / 'installed.json'
        result = _invoke([], plugins_dir, state_file)
        assert result.exit_code == 0
        assert 'random_tools' in result.output
        assert 'file_tools' in result.output
        assert 'video_tools' in result.output

    def test_default_shows_installed_and_not_installed_commands(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / 'installed.json'
        state_file.write_text(json.dumps({
            'installed_commands': {
                'organize': {'plugin': 'file_tools', 'requires': ['rich>=12.6.0']},
            }
        }))
        result = _invoke([], plugins_dir, state_file)
        assert result.exit_code == 0
        assert '+ organize' in result.output
        assert '- zip' in result.output

    def test_core_plugins_shown_as_installed(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / 'installed.json'
        result = _invoke([], plugins_dir, state_file)
        assert result.exit_code == 0
        assert '+ random' in result.output
        assert '+ crack' in result.output

    def test_installed_flag_hides_not_installed(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / 'installed.json'
        result = _invoke(['-i'], plugins_dir, state_file)
        assert result.exit_code == 0
        assert 'video_tools' not in result.output
        assert 'random_tools' in result.output

    def test_not_installed_flag_hides_installed(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / 'installed.json'
        result = _invoke(['-ni'], plugins_dir, state_file)
        assert result.exit_code == 0
        assert 'video_tools' in result.output
        assert 'random_tools' not in result.output

    def test_not_installed_flag_shows_message_when_all_installed(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / 'installed.json'
        state_file.write_text(json.dumps({
            'installed_commands': {
                'organize': {'plugin': 'file_tools', 'requires': []},
                'zip': {'plugin': 'file_tools', 'requires': []},
                'video': {'plugin': 'video_tools', 'requires': []},
            }
        }))
        result = _invoke(['-ni'], plugins_dir, state_file)
        assert result.exit_code == 0
        assert 'All available' in result.output

    def test_installed_flag_shows_message_when_nothing_installed(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / 'installed.json'
        # Remove all core commands so nothing is active
        state_file.write_text(json.dumps({
            'installed_commands': {},
            'removed_commands': ['random', 'crack'],
        }))
        result = _invoke(['-i'], plugins_dir, state_file)
        assert result.exit_code == 0
        assert 'No plugins installed' in result.output

    def test_partially_installed_plugin_shows_mixed_markers(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / 'installed.json'
        state_file.write_text(json.dumps({
            'installed_commands': {
                'organize': {'plugin': 'file_tools', 'requires': []},
            }
        }))
        result = _invoke([], plugins_dir, state_file)
        assert '+ organize' in result.output
        assert '- zip' in result.output
