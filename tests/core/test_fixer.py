import json
from unittest import mock
from click.testing import CliRunner


def _setup_state(state_file, installed_commands):
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps({'installed_commands': installed_commands}))


def _setup_plugins(plugins_dir, *plugins):
    for name, commands in plugins:
        d = plugins_dir / name
        d.mkdir()
        (d / 'manifest.json').write_text(json.dumps({'name': name, 'description': 'd', 'commands': commands}))


def _invoke(state_file, plugins_dir, pip_returncode=0):
    from lash.core.plugin_manager import make_fix_command
    cmd = make_fix_command(state_file=state_file, plugins_dir=plugins_dir)
    runner = CliRunner()
    with mock.patch('subprocess.run') as mock_run:
        mock_run.return_value = mock.MagicMock(returncode=pip_returncode, stderr='')
        result = runner.invoke(cmd, [])
    return result, mock_run


class TestFixCommand:
    def _plugins(self):
        return [
            ('file', {
                'organize': {'module': 'x:y', 'description': 'd', 'requires': ['rich>=12.6.0']},
                'zip': {'module': 'x:y', 'description': 'd', 'requires': ['pyminizip>=0.2.6', 'rich>=12.6.0']},
            }),
        ]

    def test_no_plugins_installed(self, tmp_path):
        state_file = tmp_path / 'installed.json'
        plugins_dir = tmp_path / 'plugins'
        plugins_dir.mkdir()
        _setup_state(state_file, {})
        result, mock_run = _invoke(state_file, plugins_dir)
        assert result.exit_code == 0
        assert 'No dependencies to install' in result.output
        assert "Run 'lash plugin add <plugin>' first" in result.output
        mock_run.assert_not_called()

    def test_no_dependencies_to_install(self, tmp_path):
        state_file = tmp_path / 'installed.json'
        plugins_dir = tmp_path / 'plugins'
        plugins_dir.mkdir()
        _setup_plugins(plugins_dir, ('file', {
            'organize': {'module': 'x:y', 'description': 'd', 'requires': []},
        }))
        _setup_state(state_file, {
            'organize': {'plugin': 'file', 'requires': []},
        })
        result, mock_run = _invoke(state_file, plugins_dir)
        assert result.exit_code == 0
        assert 'No dependencies to install' in result.output
        mock_run.assert_not_called()

    def test_installs_single_dependency(self, tmp_path):
        state_file = tmp_path / 'installed.json'
        plugins_dir = tmp_path / 'plugins'
        plugins_dir.mkdir()
        _setup_plugins(plugins_dir, *self._plugins())
        _setup_state(state_file, {
            'organize': {'plugin': 'file', 'requires': []},
        })
        result, mock_run = _invoke(state_file, plugins_dir)
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert 'rich>=12.6.0' in call_args

    def test_installs_multiple_dependencies(self, tmp_path):
        state_file = tmp_path / 'installed.json'
        plugins_dir = tmp_path / 'plugins'
        plugins_dir.mkdir()
        _setup_plugins(plugins_dir, ('file', {
            'organize': {'module': 'x:y', 'description': 'd', 'requires': ['rich>=12.6.0', 'pyminizip>=0.2.6']},
        }))
        _setup_state(state_file, {
            'organize': {'plugin': 'file', 'requires': []},
        })
        result, mock_run = _invoke(state_file, plugins_dir)
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert 'rich>=12.6.0' in call_args
        assert 'pyminizip>=0.2.6' in call_args

    def test_deduplicates_across_commands(self, tmp_path):
        state_file = tmp_path / 'installed.json'
        plugins_dir = tmp_path / 'plugins'
        plugins_dir.mkdir()
        _setup_plugins(plugins_dir, *self._plugins())
        _setup_state(state_file, {
            'organize': {'plugin': 'file', 'requires': []},
            'zip': {'plugin': 'file', 'requires': []},
        })
        result, mock_run = _invoke(state_file, plugins_dir)
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert call_args.count('rich>=12.6.0') == 1

    def test_installs_across_plugins(self, tmp_path):
        state_file = tmp_path / 'installed.json'
        plugins_dir = tmp_path / 'plugins'
        plugins_dir.mkdir()
        _setup_plugins(
            plugins_dir,
            ('file', {
                'organize': {'module': 'x:y', 'description': 'd', 'requires': ['rich>=12.6.0']},
            }),
            ('web', {
                'web': {'module': 'x:y', 'description': 'd', 'requires': ['bs4>=0.0.1']},
            }),
            ('device', {
                'autoclick': {'module': 'x:y', 'description': 'd', 'requires': ['pynput>=1.7.6']},
            }),
        )
        _setup_state(state_file, {
            'organize': {'plugin': 'file', 'requires': []},
            'web': {'plugin': 'web', 'requires': []},
            'autoclick': {'plugin': 'device', 'requires': []},
        })
        result, mock_run = _invoke(state_file, plugins_dir)
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert 'rich>=12.6.0' in call_args
        assert 'bs4>=0.0.1' in call_args
        assert 'pynput>=1.7.6' in call_args

    def test_pip_failure_reports_error(self, tmp_path):
        state_file = tmp_path / 'installed.json'
        plugins_dir = tmp_path / 'plugins'
        plugins_dir.mkdir()
        _setup_plugins(plugins_dir, *self._plugins())
        _setup_state(state_file, {
            'organize': {'plugin': 'file', 'requires': []},
        })
        result, _ = _invoke(state_file, plugins_dir, pip_returncode=1)
        assert result.exit_code != 0
        assert 'Dependency install failed' in result.output

    def test_handles_manifest_without_requires(self, tmp_path):
        state_file = tmp_path / 'installed.json'
        plugins_dir = tmp_path / 'plugins'
        plugins_dir.mkdir()
        _setup_plugins(plugins_dir, ('crack', {
            'crack': {'module': 'x:y', 'description': 'd'},
        }))
        _setup_state(state_file, {
            'crack': {'plugin': 'crack', 'requires': []},
        })
        result, mock_run = _invoke(state_file, plugins_dir)
        assert result.exit_code == 0
        assert 'No dependencies to install' in result.output
        mock_run.assert_not_called()

    def test_state_file_does_not_exist(self, tmp_path):
        state_file = tmp_path / 'installed.json'
        plugins_dir = tmp_path / 'plugins'
        plugins_dir.mkdir()
        result, mock_run = _invoke(state_file, plugins_dir)
        assert result.exit_code == 0
        assert 'No dependencies to install' in result.output
        mock_run.assert_not_called()
