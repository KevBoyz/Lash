# pytest lash/plugins/macro/tests/test_cli.py
from pathlib import Path


class TestMacroCommand:
    def test_record_flag_calls_record_macro(self, tmp_path, monkeypatch):
        from unittest.mock import patch
        from click.testing import CliRunner

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        mock_ret = {"name": "x", "duration": 1.0, "events": [1]}
        with (
            patch(
                "lash.plugins.macro.cli.record_macro", return_value=mock_ret
            ) as mock_rec,
            patch("lash.plugins.macro.cli.minimize_terminal"),
        ):
            from lash.plugins.macro.cli import macro

            result = CliRunner().invoke(macro, ["-r", "x"])
        assert result.exit_code == 0
        mock_rec.assert_called_once_with("x")
        assert "saved" in result.output

    def test_record_existing_macro_shows_error(self, tmp_path, monkeypatch):
        from unittest.mock import patch
        from click.testing import CliRunner

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        with patch(
            "lash.plugins.macro.cli.record_macro",
            side_effect=ValueError("already exists"),
        ):
            from lash.plugins.macro.cli import macro

            result = CliRunner().invoke(macro, ["-r", "x"])
        assert result.exit_code != 0
        assert "already exists" in result.output

    def test_play_flag_calls_play_macro(self, tmp_path, monkeypatch):
        from unittest.mock import patch
        from click.testing import CliRunner

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        with (
            patch("lash.plugins.macro.cli.play_macro") as mock_play,
            patch("lash.plugins.macro.cli.minimize_terminal"),
        ):
            from lash.plugins.macro.cli import macro

            result = CliRunner().invoke(macro, ["-p", "x"])
        assert result.exit_code == 0
        mock_play.assert_called_once_with(
            "x", speed=1.0, full_speed=False, repeat=1, loop=False
        )

    def test_play_not_found_shows_error(self, tmp_path, monkeypatch):
        from unittest.mock import patch
        from click.testing import CliRunner

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        with patch(
            "lash.plugins.macro.cli.play_macro", side_effect=ValueError("not found")
        ):
            from lash.plugins.macro.cli import macro

            result = CliRunner().invoke(macro, ["-p", "ghost"])
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_list_flag_shows_macros(self, tmp_path, monkeypatch):
        from unittest.mock import patch
        from click.testing import CliRunner

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        fake = [{"name": "login", "created_at": "2026-05-15T14:32:00", "duration": 4.8}]
        with patch("lash.plugins.macro.cli.list_macros", return_value=fake):
            from lash.plugins.macro.cli import macro

            result = CliRunner().invoke(macro, ["-l"])
        assert result.exit_code == 0
        assert "login" in result.output
        assert "4.8" in result.output

    def test_list_empty_shows_message(self, tmp_path, monkeypatch):
        from unittest.mock import patch
        from click.testing import CliRunner

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        with patch("lash.plugins.macro.cli.list_macros", return_value=[]):
            from lash.plugins.macro.cli import macro

            result = CliRunner().invoke(macro, ["-l"])
        assert result.exit_code == 0
        assert "No macros" in result.output

    def test_rename_calls_rename_macro(self, tmp_path, monkeypatch):
        from unittest.mock import patch
        from click.testing import CliRunner

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        with patch("lash.plugins.macro.cli.rename_macro") as mock_ren:
            from lash.plugins.macro.cli import macro

            result = CliRunner().invoke(macro, ["--rename", "old", "new"])
        assert result.exit_code == 0
        mock_ren.assert_called_once_with("old", "new")
        assert "renamed" in result.output

    def test_delete_calls_delete_macro(self, tmp_path, monkeypatch):
        from unittest.mock import patch
        from click.testing import CliRunner

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        with patch("lash.plugins.macro.cli.delete_macro") as mock_del:
            from lash.plugins.macro.cli import macro

            result = CliRunner().invoke(macro, ["-d", "x"])
        assert result.exit_code == 0
        mock_del.assert_called_once_with("x")
        assert "deleted" in result.output

    def test_no_action_flag_shows_usage_error(self, tmp_path, monkeypatch):
        from click.testing import CliRunner

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        from lash.plugins.macro.cli import macro

        result = CliRunner().invoke(macro, [])
        assert result.exit_code != 0

    def test_speed_and_full_speed_mutually_exclusive(self, tmp_path, monkeypatch):
        from unittest.mock import patch
        from click.testing import CliRunner

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        with patch("lash.plugins.macro.cli.play_macro"):
            from lash.plugins.macro.cli import macro

            result = CliRunner().invoke(
                macro, ["-p", "x", "--speed", "2.0", "--full-speed"]
            )
        assert result.exit_code != 0

    def test_loop_and_n_mutually_exclusive(self, tmp_path, monkeypatch):
        from unittest.mock import patch
        from click.testing import CliRunner

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        with patch("lash.plugins.macro.cli.play_macro"):
            from lash.plugins.macro.cli import macro

            result = CliRunner().invoke(macro, ["-p", "x", "--loop", "-n", "3"])
        assert result.exit_code != 0

    def test_record_without_name_shows_error(self, tmp_path, monkeypatch):
        from click.testing import CliRunner

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        from lash.plugins.macro.cli import macro

        result = CliRunner().invoke(macro, ["-r"])
        assert result.exit_code != 0

    def test_play_without_name_shows_error(self, tmp_path, monkeypatch):
        from click.testing import CliRunner

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        from lash.plugins.macro.cli import macro

        result = CliRunner().invoke(macro, ["-p"])
        assert result.exit_code != 0

    def test_delete_without_name_shows_error(self, tmp_path, monkeypatch):
        from click.testing import CliRunner

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        from lash.plugins.macro.cli import macro

        result = CliRunner().invoke(macro, ["-d"])
        assert result.exit_code != 0

    def test_rename_with_only_one_arg_shows_error(self, tmp_path, monkeypatch):
        from click.testing import CliRunner

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        from lash.plugins.macro.cli import macro

        result = CliRunner().invoke(macro, ["--rename", "old"])
        assert result.exit_code != 0

    def test_play_negative_speed_shows_error(self, tmp_path, monkeypatch):
        from click.testing import CliRunner

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        from lash.plugins.macro.cli import macro

        result = CliRunner().invoke(macro, ["-p", "x", "--speed", "-1"])
        assert result.exit_code != 0
