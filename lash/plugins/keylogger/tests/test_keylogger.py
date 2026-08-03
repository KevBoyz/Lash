# pytest lash/plugins/keylogger/tests/test_keylogger.py
import os
import pytest
from unittest.mock import MagicMock, patch


class TestKeyDown:
    def test_writes_char_to_file(self, tmp_path):
        from lash.plugins.keylogger.core import key_down

        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)

            class FakeKey:
                char = "a"

            key_down(FakeKey())
            log_path = tmp_path / "Keylogger.txt"
            assert log_path.exists()
            assert log_path.read_text() == "a"
        finally:
            os.chdir(original_dir)

    def test_writes_multiple_chars_appends(self, tmp_path):
        from lash.plugins.keylogger.core import key_down

        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)

            class FakeKey:
                def __init__(self, c):
                    self.char = c

            key_down(FakeKey("h"))
            key_down(FakeKey("i"))
            log_path = tmp_path / "Keylogger.txt"
            assert log_path.read_text() == "hi"
        finally:
            os.chdir(original_dir)

    def test_writes_space_for_space_key(self, tmp_path):
        from lash.plugins.keylogger.core import key_down
        from pynput.keyboard import Key

        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            key_down(Key.space)
            log_path = tmp_path / "Keylogger.txt"
            assert log_path.read_text() == " "
        finally:
            os.chdir(original_dir)

    def test_writes_backspace_marker(self, tmp_path):
        from lash.plugins.keylogger.core import key_down
        from pynput.keyboard import Key

        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            key_down(Key.backspace)
            log_path = tmp_path / "Keylogger.txt"
            assert " <bkp> " in log_path.read_text()
        finally:
            os.chdir(original_dir)

    def test_writes_enter_marker(self, tmp_path):
        from lash.plugins.keylogger.core import key_down
        from pynput.keyboard import Key

        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            key_down(Key.enter)
            log_path = tmp_path / "Keylogger.txt"
            content = log_path.read_text()
            assert " <enter> " in content
            assert "\n" in content
        finally:
            os.chdir(original_dir)

    def test_writes_unknown_key_with_angle_brackets(self, tmp_path):
        from lash.plugins.keylogger.core import key_down
        from pynput.keyboard import Key

        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            key_down(Key.f1)
            log_path = tmp_path / "Keylogger.txt"
            content = log_path.read_text()
            assert content.startswith(" <") and content.endswith("> ")
        finally:
            os.chdir(original_dir)


class TestKeyUp:
    def test_f3_returns_false(self):
        from lash.plugins.keylogger.core import key_up
        from pynput.keyboard import Key

        result = key_up(Key.f3)
        assert result is False

    def test_other_key_returns_none(self):
        from lash.plugins.keylogger.core import key_up
        from pynput.keyboard import Key

        result = key_up(Key.enter)
        assert result is None

    def test_letter_key_returns_none(self):
        from lash.plugins.keylogger.core import key_up
        from pynput.keyboard import Key

        result = key_up(Key.space)
        assert result is None


class TestKeyloggerCommand:
    @pytest.mark.skip(
        reason=(
            "keylogger command starts a blocking pynput Listener — "
            "cannot be tested without a real display/input device."
        )
    )
    def test_keylogger_command_skipped(self):
        pass
