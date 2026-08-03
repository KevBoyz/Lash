import json
import pathlib
import sys
from unittest import mock
from click.testing import CliRunner


def _setup_state(state_file, installed_commands):
    pathlib.Path(state_file).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(state_file).write_text(
        json.dumps({"installed_commands": installed_commands})
    )


def _fake_run(returncode):
    m = mock.MagicMock()
    m.returncode = returncode
    m.stderr = ""
    return m


def _setup_plugins(tmp_path):
    for name, commands in [
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
                    "requires": ["pyminizip>=0.2.6", "rich>=12.6.0"],
                },
            },
        ),
        (
            "web",
            {
                "web": {
                    "module": "lash.plugins.web.cli:web",
                    "description": "d",
                    "requires": ["bs4>=0.0.1", "rich>=12.6.0"],
                },
            },
        ),
    ]:
        d = tmp_path / name
        d.mkdir()
        (d / "manifest.json").write_text(json.dumps(
            {"name": name, "description": "d", "commands": commands}))
    return tmp_path


def _invoke(plugins, plugins_dir, state_file, pip_returncode=0):
    from lash.core.plugin_manager import make_remove_command

    cmd = make_remove_command(plugins_dir=plugins_dir, state_file=state_file)
    runner = CliRunner()
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.MagicMock(
            returncode=pip_returncode, stderr="")
        result = runner.invoke(cmd, list(plugins))
    return result, mock_run


def _invoke_group(command, plugins, plugins_dir, state_file, pip_returncode=0):
    from lash.core.plugin_manager import make_plugin_group

    group = make_plugin_group(plugins_dir=plugins_dir, state_file=state_file)
    runner = CliRunner()
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.MagicMock(
            returncode=pip_returncode, stderr="")
        result = runner.invoke(group, [command] + list(plugins))
    return result, mock_run


class TestUninstallAlias:
    def test_removes_plugin_como_uninstall(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        _setup_state(
            state_file,
            {
                "organize": {"plugin": "file", "requires": ["rich>=12.6.0"]},
                "zip": {
                    "plugin": "file",
                    "requires": ["pyminizip>=0.2.6", "rich>=12.6.0"],
                },
            },
        )
        result, _ = _invoke_group(
            "uninstall", ["file"], plugins_dir, state_file)
        assert result.exit_code == 0
        state = json.loads(state_file.read_text())
        assert "organize" not in state["installed_commands"]
        assert "zip" not in state["installed_commands"]

    def test_alias_nao_duplica_no_help(self, tmp_path):
        from lash.core.plugin_manager import make_plugin_group

        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        group = make_plugin_group(
            plugins_dir=plugins_dir,
            state_file=state_file)
        runner = CliRunner()
        result = runner.invoke(group, ["--help"])
        assert result.exit_code == 0
        assert "remove" in result.output
        assert "  uninstall" not in result.output

    def test_help_do_remove_anuncia_alias_uninstall(self, tmp_path):
        from lash.core.plugin_manager import make_plugin_group

        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        group = make_plugin_group(
            plugins_dir=plugins_dir,
            state_file=state_file)
        runner = CliRunner()
        result = runner.invoke(group, ["remove", "--help"])
        assert result.exit_code == 0
        assert "Alias: uninstall" in result.output


class TestRemoveAll:
    def test_removes_all_commands_of_plugin(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        _setup_state(
            state_file,
            {
                "organize": {"plugin": "file", "requires": ["rich>=12.6.0"]},
                "zip": {
                    "plugin": "file",
                    "requires": ["pyminizip>=0.2.6", "rich>=12.6.0"],
                },
            },
        )
        result, _ = _invoke(["file"], plugins_dir, state_file)
        assert result.exit_code == 0
        state = json.loads(state_file.read_text())
        assert "organize" not in state["installed_commands"]
        assert "zip" not in state["installed_commands"]

    def test_uninstalls_orphaned_deps(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        _setup_state(
            state_file,
            {
                "organize": {"plugin": "file", "requires": ["rich>=12.6.0"]},
                "zip": {
                    "plugin": "file",
                    "requires": ["pyminizip>=0.2.6", "rich>=12.6.0"],
                },
            },
        )
        result, mock_run = _invoke(["file"], plugins_dir, state_file)
        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "rich" in " ".join(call_args)
        assert "pyminizip" in " ".join(call_args)

    def test_preserves_deps_used_by_other_plugins(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        _setup_state(
            state_file, {
                "organize": {
                    "plugin": "file", "requires": ["rich>=12.6.0"]}, "web": {
                    "plugin": "web", "requires": [
                        "bs4>=0.0.1", "rich>=12.6.0"]}, }, )
        result, mock_run = _invoke(["file"], plugins_dir, state_file)
        assert result.exit_code == 0
        if mock_run.called:
            call_args = mock_run.call_args[0][0]
            assert "rich" not in call_args

    def test_nothing_to_remove_exits_cleanly(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        _setup_state(state_file, {})
        result, _ = _invoke(["file"], plugins_dir, state_file)
        assert result.exit_code == 0
        assert (
            "nothing" in result.output.lower()
            or "not installed" in result.output.lower()
        )

    def test_removes_multiple_plugins_in_one_call(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        _setup_state(
            state_file, {
                "organize": {
                    "plugin": "file", "requires": ["rich>=12.6.0"]}, "zip": {
                    "plugin": "file", "requires": [
                        "pyminizip>=0.2.6", "rich>=12.6.0"], }, "web": {
                        "plugin": "web", "requires": [
                            "bs4>=0.0.1", "rich>=12.6.0"]}, }, )
        result, _ = _invoke(["file", "web"], plugins_dir, state_file)
        assert result.exit_code == 0
        state = json.loads(state_file.read_text())
        assert "organize" not in state["installed_commands"]
        assert "zip" not in state["installed_commands"]
        assert "web" not in state["installed_commands"]


class TestRemoveErrors:
    def test_unknown_plugin_fails(self, tmp_path):
        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        _setup_state(state_file, {})
        result, _ = _invoke(["nonexistent_plugin"], plugins_dir, state_file)
        assert result.exit_code != 0
        assert "Unknown plugin" in result.output


class TestUninstallerDetection:
    def test_usa_uv_quando_pip_indisponivel(self, tmp_path):
        from lash.core.plugin_manager import make_remove_command

        plugins_dir = _setup_plugins(tmp_path)
        state_file = tmp_path / "installed.json"
        _setup_state(
            state_file,
            {
                "organize": {"plugin": "file", "requires": ["rich>=12.6.0"]},
                "zip": {
                    "plugin": "file",
                    "requires": ["pyminizip>=0.2.6", "rich>=12.6.0"],
                },
            },
        )
        cmd = make_remove_command(
            plugins_dir=plugins_dir,
            state_file=state_file)
        runner = CliRunner()
        with (
            mock.patch(
                "subprocess.run", side_effect=[_fake_run(1), _fake_run(0)]
            ) as mock_run,
            mock.patch("shutil.which", return_value="uv"),
        ):
            result = runner.invoke(cmd, ["file"])
        assert result.exit_code == 0
        uninstall_args = mock_run.call_args_list[1][0][0]
        assert uninstall_args[0:5] == [
            "uv",
            "pip",
            "uninstall",
            "--python",
            sys.executable,
        ]
        assert "rich" in uninstall_args
        assert "pyminizip" in uninstall_args
