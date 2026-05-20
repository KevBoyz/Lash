# pytest lash/plugins/device/tests/test_device.py
import os
import pytest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner


class TestKeyDown:
    def test_writes_char_to_file(self, tmp_path):
        from lash.plugins.device.core import key_down
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)

            class FakeKey:
                char = 'a'

            key_down(FakeKey())
            log_path = tmp_path / 'Keylogger.txt'
            assert log_path.exists()
            assert log_path.read_text() == 'a'
        finally:
            os.chdir(original_dir)

    def test_writes_multiple_chars_appends(self, tmp_path):
        from lash.plugins.device.core import key_down
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)

            class FakeKey:
                def __init__(self, c):
                    self.char = c

            key_down(FakeKey('h'))
            key_down(FakeKey('i'))
            log_path = tmp_path / 'Keylogger.txt'
            assert log_path.read_text() == 'hi'
        finally:
            os.chdir(original_dir)

    def test_writes_space_for_space_key(self, tmp_path):
        from lash.plugins.device.core import key_down
        from pynput.keyboard import Key
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            key_down(Key.space)
            log_path = tmp_path / 'Keylogger.txt'
            assert log_path.read_text() == ' '
        finally:
            os.chdir(original_dir)

    def test_writes_backspace_marker(self, tmp_path):
        from lash.plugins.device.core import key_down
        from pynput.keyboard import Key
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            key_down(Key.backspace)
            log_path = tmp_path / 'Keylogger.txt'
            assert ' <bkp> ' in log_path.read_text()
        finally:
            os.chdir(original_dir)

    def test_writes_enter_marker(self, tmp_path):
        from lash.plugins.device.core import key_down
        from pynput.keyboard import Key
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            key_down(Key.enter)
            log_path = tmp_path / 'Keylogger.txt'
            content = log_path.read_text()
            assert ' <enter> ' in content
            assert '\n' in content
        finally:
            os.chdir(original_dir)

    def test_writes_unknown_key_with_angle_brackets(self, tmp_path):
        from lash.plugins.device.core import key_down
        from pynput.keyboard import Key
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            key_down(Key.f1)
            log_path = tmp_path / 'Keylogger.txt'
            content = log_path.read_text()
            assert content.startswith(' <') and content.endswith('> ')
        finally:
            os.chdir(original_dir)


class TestKeyUp:
    def test_f3_returns_false(self):
        from lash.plugins.device.core import key_up
        from pynput.keyboard import Key
        result = key_up(Key.f3)
        assert result is False

    def test_other_key_returns_none(self):
        from lash.plugins.device.core import key_up
        from pynput.keyboard import Key
        result = key_up(Key.enter)
        assert result is None

    def test_letter_key_returns_none(self):
        from lash.plugins.device.core import key_up
        from pynput.keyboard import Key
        result = key_up(Key.space)
        assert result is None


class TestKeyloggerCommand:
    @pytest.mark.skip(reason=(
        "keylogger command starts a blocking pynput Listener — "
        "cannot be tested without a real display/input device."
    ))
    def test_keylogger_command_skipped(self):
        pass


class TestRunAutoclickSingle:
    def test_presses_and_releases_left_button(self):
        from lash.plugins.device.core import run_autoclick_single

        mock_button = MagicMock()
        mock_button.left = 'left'
        mock_controller_instance = MagicMock()
        mock_controller_cls = MagicMock(return_value=mock_controller_instance)

        with patch.dict('sys.modules', {
            'pynput': MagicMock(),
            'pynput.mouse': MagicMock(Controller=mock_controller_cls, Button=mock_button),
        }):
            run_autoclick_single()

        mock_controller_instance.press.assert_called_once_with(mock_button.left)
        mock_controller_instance.release.assert_called_once_with(mock_button.left)


class TestRunAutoclickDouble:
    def test_presses_and_releases_twice(self):
        from lash.plugins.device.core import run_autoclick_double

        mock_button = MagicMock()
        mock_button.left = 'left'
        mock_controller_instance = MagicMock()
        mock_controller_cls = MagicMock(return_value=mock_controller_instance)

        with patch.dict('sys.modules', {
            'pynput': MagicMock(),
            'pynput.mouse': MagicMock(Controller=mock_controller_cls, Button=mock_button),
        }):
            run_autoclick_double()

        assert mock_controller_instance.press.call_count == 2
        assert mock_controller_instance.release.call_count == 2
        mock_controller_instance.press.assert_called_with(mock_button.left)
        mock_controller_instance.release.assert_called_with(mock_button.left)


class TestRunKeyholdInfiniteLoop:
    @pytest.mark.skip(reason="requires physical keyboard input — infinite loop until F3 is pressed")
    def test_run_keyhold(self):
        pass


class TestRunAutoclickHoldInfiniteLoop:
    @pytest.mark.skip(reason="requires physical mouse/keyboard input — infinite loop until F4/F3 are pressed")
    def test_run_autoclick_hold(self):
        pass


class TestRunAutoclickRepeatInfiniteLoop:
    @pytest.mark.skip(reason="requires physical keyboard input — infinite loop driven by F4/F3 keypresses")
    def test_run_autoclick_repeat(self):
        pass


class TestAutoclickCommand:
    def test_single_click_flag(self):
        with patch('lash.plugins.device.cli.run_autoclick_single') as mock_sg, \
             patch('lash.plugins.device.cli.run_autoclick_double'), \
             patch('lash.plugins.device.cli.run_autoclick_hold'), \
             patch('lash.plugins.device.cli.run_autoclick_repeat'):
            from lash.plugins.device.cli import autoclick
            runner = CliRunner()
            result = runner.invoke(autoclick, ['-sg'])
            assert result.exit_code == 0
            mock_sg.assert_called_once()

    def test_double_click_flag(self):
        with patch('lash.plugins.device.cli.run_autoclick_single'), \
             patch('lash.plugins.device.cli.run_autoclick_double') as mock_db, \
             patch('lash.plugins.device.cli.run_autoclick_hold'), \
             patch('lash.plugins.device.cli.run_autoclick_repeat'):
            from lash.plugins.device.cli import autoclick
            runner = CliRunner()
            result = runner.invoke(autoclick, ['-db'])
            assert result.exit_code == 0
            mock_db.assert_called_once()

    def test_no_flags_prints_message(self):
        with patch('lash.plugins.device.cli.run_autoclick_single'), \
             patch('lash.plugins.device.cli.run_autoclick_double'), \
             patch('lash.plugins.device.cli.run_autoclick_hold'), \
             patch('lash.plugins.device.cli.run_autoclick_repeat') as mock_repeat, \
             patch('lash.plugins.device.cli.is_pressed', return_value=False):
            from lash.plugins.device.cli import autoclick
            runner = CliRunner()
            result = runner.invoke(autoclick, [])
            assert result.exit_code == 0
            assert 'Auto Clicker initialized' in result.output
            mock_repeat.assert_called_once_with(0.0)

    def test_ch_flag_prints_hold_message(self):
        with patch('lash.plugins.device.cli.run_autoclick_single'), \
             patch('lash.plugins.device.cli.run_autoclick_double'), \
             patch('lash.plugins.device.cli.run_autoclick_hold') as mock_hold, \
             patch('lash.plugins.device.cli.run_autoclick_repeat'), \
             patch('lash.plugins.device.cli.is_pressed', return_value=False):
            from lash.plugins.device.cli import autoclick
            runner = CliRunner()
            result = runner.invoke(autoclick, ['-ch'])
            assert result.exit_code == 0
            assert '*click* to stop' in result.output
            mock_hold.assert_called_once()
