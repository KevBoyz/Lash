import json
import sys
from unittest import mock
from click.testing import CliRunner


def _fake_run(returncode):
    m = mock.MagicMock()
    m.returncode = returncode
    m.stderr = ""
    return m


def _setup_plugins(tmp_path):
    for name, commands in [
        (
            "crack",
            {
                "crack": {
                    "module": "lash.plugins.crack.cli:crack",
                    "description": "d",
                    "requires": [],
                },
            },
        ),
        (
            "file",
            {
                "organize": {
                    "module": "lash.plugins.file.cli:organize",
                    "description": "d",
                    "requires": ["rich>=12.6.0"],
                },
                "zip": {
                    "module": "lash.plugins.file.cli:zip_group",
                    "description": "d",
                    "requires": ["pyzipper>=0.2.6", "rich>=12.6.0"],
                },
            },
        ),
        (
            "device",
            {
                "autoclick": {
                    "module": "lash.plugins.device.cli:autoclick",
                    "description": "d",
                    "requires": ["pynput>=1.7.6"],
                },
                "keyhold": {
                    "module": "lash.plugins.device.cli:keyhold",
                    "description": "d",
                    "requires": ["pynput>=1.7.6"],
                },
            },
        ),
    ]:
        d = tmp_path / name
        d.mkdir()
        (d / "manifest.json").write_text(
            json.dumps({"name": name, "description": "d", "commands": commands})
        )
    return tmp_path


def _invoke(plugins, plugins_dir, state_file, pip_returncode=0):
    from lash.core.plugin_manager import make_download_command

    cmd = make_download_command(plugins_dir=plugins_dir, state_file=state_file)
    runner = CliRunner()
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.MagicMock(returncode=pip_returncode, stderr="")
        result = runner.invoke(cmd, list(plugins))
    return result, mock_run


def _invoke_group(command, plugins, plugins_dir, state_file, pip_returncode=0):
    from lash.core.plugin_manager import make_plugin_group

    group = make_plugin_group(plugins_dir=plugins_dir, state_file=state_file)
    runner = CliRunner()
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.MagicMock(returncode=pip_returncode, stderr="")
        result = runner.invoke(group, [command] + list(plugins))
    return result, mock_run


class TestInstallAlias:
    def test_installs_plugin_como_install(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        result, _ = _invoke_group("install", ["file"], plugins_dir, state_file)
        assert result.exit_code == 0
        state = json.loads(state_file.read_text())
        assert "organize" in state["installed_commands"]
        assert "zip" in state["installed_commands"]

    def test_alias_nao_duplica_no_help(self, tmp_path):
        from lash.core.plugin_manager import make_plugin_group

        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        group = make_plugin_group(plugins_dir=plugins_dir, state_file=state_file)
        runner = CliRunner()
        result = runner.invoke(group, ["--help"])
        assert result.exit_code == 0
        assert "add" in result.output
        assert "  install" not in result.output

    def test_help_do_add_anuncia_alias_install(self, tmp_path):
        from lash.core.plugin_manager import make_plugin_group

        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        group = make_plugin_group(plugins_dir=plugins_dir, state_file=state_file)
        runner = CliRunner()
        result = runner.invoke(group, ["add", "--help"])
        assert result.exit_code == 0
        assert "Alias: install" in result.output


class TestDownloadAll:
    def test_installs_all_commands_of_plugin(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        result, _ = _invoke(["file"], plugins_dir, state_file)
        assert result.exit_code == 0
        state = json.loads(state_file.read_text())
        assert "organize" in state["installed_commands"]
        assert "zip" in state["installed_commands"]

    def test_no_pip_call_when_zero_deps(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        result, mock_run = _invoke(["crack"], plugins_dir, state_file)
        assert result.exit_code == 0
        mock_run.assert_not_called()

    def test_pip_called_with_deduplicated_requires(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        result, mock_run = _invoke(["file"], plugins_dir, state_file)
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert call_args.count("rich>=12.6.0") == 1

    def test_skips_already_installed_commands(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        state_file.write_text(
            json.dumps(
                {
                    "installed_commands": {
                        "organize": {
                            "plugin": "file",
                            "requires": ["rich>=12.6.0"],
                        }
                    }
                }
            )
        )
        result, _ = _invoke(["file"], plugins_dir, state_file)
        assert result.exit_code == 0
        state = json.loads(state_file.read_text())
        assert "zip" in state["installed_commands"]

    def test_installs_multiple_plugins_in_one_call(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        result, _ = _invoke(["crack", "device"], plugins_dir, state_file)
        assert result.exit_code == 0
        state = json.loads(state_file.read_text())
        assert "autoclick" in state["installed_commands"]
        assert "keyhold" in state["installed_commands"]


class TestDownloadErrors:
    def test_unknown_plugin_fails(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        result, _ = _invoke(["nonexistent_plugin"], plugins_dir, state_file)
        assert result.exit_code != 0
        assert "Unknown plugin" in result.output

    def test_lists_available_plugins_on_unknown(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        result, _ = _invoke(["bogus"], plugins_dir, state_file)
        assert "file" in result.output or "crack" in result.output

    def test_pip_failure_skips_plugin_and_does_not_mark_installed(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        result, _ = _invoke(["file"], plugins_dir, state_file, pip_returncode=1)
        assert result.exit_code == 0
        assert not state_file.exists() or "organize" not in json.loads(
            state_file.read_text()
        ).get("installed_commands", {})

    def test_pip_failure_does_not_break_other_plugins(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        result, _ = _invoke(
            ["crack", "file"], plugins_dir, state_file, pip_returncode=1
        )
        assert result.exit_code == 0
        state = json.loads(state_file.read_text())
        assert "crack" in state["installed_commands"]
        assert "organize" not in state["installed_commands"]


class TestInstallerDetection:
    def test_usa_uv_quando_pip_indisponivel(self, tmp_path):
        from lash.core.plugin_manager import make_download_command

        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        cmd = make_download_command(plugins_dir=plugins_dir, state_file=state_file)
        runner = CliRunner()
        with (
            mock.patch(
                "subprocess.run", side_effect=[_fake_run(1), _fake_run(0)]
            ) as mock_run,
            mock.patch("shutil.which", return_value="uv"),
        ):
            result = runner.invoke(cmd, ["file"])
        assert result.exit_code == 0
        install_args = mock_run.call_args_list[1][0][0]
        assert install_args[0:5] == [
            "uv",
            "pip",
            "install",
            "--python",
            sys.executable,
        ]
        assert "rich>=12.6.0" in install_args
        assert "pyzipper>=0.2.6" in install_args

    def test_erro_quando_pip_e_uv_indisponiveis(self, tmp_path):
        from lash.core.plugin_manager import make_download_command

        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        cmd = make_download_command(plugins_dir=plugins_dir, state_file=state_file)
        runner = CliRunner()
        with (
            mock.patch("subprocess.run", return_value=_fake_run(1)),
            mock.patch("shutil.which", return_value=None),
        ):
            result = runner.invoke(cmd, ["file"])
        assert result.exit_code == 0
        assert "No package installer found" in result.output
        assert "pip install" in result.output
        assert "rich>=12.6.0" in result.output
        assert "pyzipper>=0.2.6" in result.output
