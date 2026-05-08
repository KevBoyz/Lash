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

    def test_available_flag_does_not_show_fully_installed_in_not_installed_section(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / 'installed.json'
        state_file.write_text(json.dumps({
            'installed_commands': {
                'organize': {'plugin': 'file_tools', 'requires': []},
                'zip': {'plugin': 'file_tools', 'requires': []},
            }
        }))
        result = _invoke(['--available'], plugins_dir, state_file)
        not_installed_section = result.output.split('Not installed')[-1] if 'Not installed' in result.output else ''
        assert 'file_tools' not in not_installed_section

    def test_no_plugins_installed_message(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / 'installed.json'
        result = _invoke([], plugins_dir, state_file)
        assert 'No plugins installed' in result.output or 'lash download' in result.output
