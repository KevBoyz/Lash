# pytest lash/plugins/device/tests/test_device.py
import pytest
from unittest.mock import MagicMock, patch, call
from click.testing import CliRunner


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
