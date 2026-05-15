# pytest lash/plugins/device/tests/test_macro.py
import json
from pathlib import Path


class TestGetDataDir:
    def test_returns_path_under_lash(self, tmp_path, monkeypatch):
        from lash.plugins.device.helpers import get_data_dir
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        result = get_data_dir()
        assert result == tmp_path / '.lash' / 'data' / 'device'

    def test_creates_directory_if_missing(self, tmp_path, monkeypatch):
        from lash.plugins.device.helpers import get_data_dir
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        result = get_data_dir()
        assert result.exists()


class TestMacroPath:
    def test_returns_json_path(self, tmp_path, monkeypatch):
        from lash.plugins.device.helpers import macro_path
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        result = macro_path('login')
        assert result == tmp_path / '.lash' / 'data' / 'device' / 'login.json'


class TestSaveAndLoadMacro:
    def test_roundtrip(self, tmp_path, monkeypatch):
        from lash.plugins.device.helpers import save_macro, load_macro
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        data = {
            'name': 'test',
            'created_at': '2026-05-15T10:00:00',
            'duration': 1.5,
            'events': [{'t': 0.0, 'type': 'key_down', 'key': 'a'}],
        }
        save_macro('test', data)
        result = load_macro('test')
        assert result == data

    def test_load_raises_when_not_found(self, tmp_path, monkeypatch):
        import pytest
        from lash.plugins.device.helpers import load_macro
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        with pytest.raises(FileNotFoundError):
            load_macro('missing')


class TestListMacroFiles:
    def test_returns_empty_when_no_macros(self, tmp_path, monkeypatch):
        from lash.plugins.device.helpers import list_macro_files
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        assert list_macro_files() == []

    def test_returns_sorted_by_created_at_descending(self, tmp_path, monkeypatch):
        from lash.plugins.device.helpers import save_macro, list_macro_files
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        save_macro('old', {'name': 'old', 'created_at': '2026-05-14T09:00:00', 'duration': 1.0, 'events': []})
        save_macro('new', {'name': 'new', 'created_at': '2026-05-15T10:00:00', 'duration': 2.0, 'events': []})
        result = list_macro_files()
        assert [r['name'] for r in result] == ['new', 'old']


class TestRenameMacroFile:
    def test_renames_file_and_updates_name_field(self, tmp_path, monkeypatch):
        import pytest
        from lash.plugins.device.helpers import save_macro, rename_macro_file, load_macro
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        save_macro('old', {'name': 'old', 'created_at': '2026-05-15T10:00:00', 'duration': 1.0, 'events': []})
        rename_macro_file('old', 'new')
        result = load_macro('new')
        assert result['name'] == 'new'
        with pytest.raises(FileNotFoundError):
            load_macro('old')

    def test_raises_when_source_not_found(self, tmp_path, monkeypatch):
        import pytest
        from lash.plugins.device.helpers import rename_macro_file
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        with pytest.raises(FileNotFoundError):
            rename_macro_file('missing', 'new')

    def test_raises_when_target_exists(self, tmp_path, monkeypatch):
        import pytest
        from lash.plugins.device.helpers import save_macro, rename_macro_file
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        save_macro('a', {'name': 'a', 'created_at': '2026-05-15T10:00:00', 'duration': 1.0, 'events': []})
        save_macro('b', {'name': 'b', 'created_at': '2026-05-15T10:00:00', 'duration': 1.0, 'events': []})
        with pytest.raises(FileExistsError):
            rename_macro_file('a', 'b')


class TestDeleteMacroFile:
    def test_deletes_existing_macro(self, tmp_path, monkeypatch):
        import pytest
        from lash.plugins.device.helpers import save_macro, delete_macro_file, load_macro
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        save_macro('bye', {'name': 'bye', 'created_at': '2026-05-15T10:00:00', 'duration': 1.0, 'events': []})
        delete_macro_file('bye')
        with pytest.raises(FileNotFoundError):
            load_macro('bye')

    def test_raises_when_not_found(self, tmp_path, monkeypatch):
        import pytest
        from lash.plugins.device.helpers import delete_macro_file
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        with pytest.raises(FileNotFoundError):
            delete_macro_file('missing')


class TestSerializeKey:
    def test_regular_char(self):
        from lash.plugins.device.helpers import serialize_key
        from unittest.mock import MagicMock
        key = MagicMock(spec=[])
        key.char = 'a'
        assert serialize_key(key) == 'a'

    def test_special_key(self):
        from lash.plugins.device.helpers import serialize_key
        from unittest.mock import MagicMock
        import pynput.keyboard as kb
        assert serialize_key(kb.Key.shift) == 'Key.shift'

    def test_unknown_key_returns_none(self):
        from lash.plugins.device.helpers import serialize_key
        from unittest.mock import MagicMock
        key = MagicMock()
        key.char = None  # pynput KeyCode with no printable char
        assert serialize_key(key) is None


class TestDeserializeKey:
    def test_regular_char(self):
        from lash.plugins.device.helpers import deserialize_key
        import pynput.keyboard as kb
        result = deserialize_key('a')
        assert result == 'a'

    def test_special_key(self):
        from lash.plugins.device.helpers import deserialize_key
        import pynput.keyboard as kb
        result = deserialize_key('Key.shift')
        assert result == kb.Key.shift


class TestMinimizeTerminal:
    def test_does_not_raise_on_any_platform(self):
        from lash.plugins.device.helpers import minimize_terminal
        minimize_terminal()


class TestListMacros:
    def test_returns_formatted_list(self, tmp_path, monkeypatch):
        from lash.plugins.device.helpers import save_macro
        from lash.plugins.device.core import list_macros
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        save_macro('login', {'name': 'login', 'created_at': '2026-05-15T14:32:00', 'duration': 4.821, 'events': []})
        result = list_macros()
        assert len(result) == 1
        assert result[0]['name'] == 'login'
        assert result[0]['duration'] == 4.821
        assert result[0]['created_at'] == '2026-05-15T14:32:00'

    def test_returns_empty_list_when_no_macros(self, tmp_path, monkeypatch):
        from lash.plugins.device.core import list_macros
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        assert list_macros() == []


class TestRenameMacro:
    def test_renames_successfully(self, tmp_path, monkeypatch):
        from lash.plugins.device.helpers import save_macro, load_macro
        from lash.plugins.device.core import rename_macro
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        save_macro('old', {'name': 'old', 'created_at': '2026-05-15T10:00:00', 'duration': 1.0, 'events': []})
        rename_macro('old', 'new')
        assert load_macro('new')['name'] == 'new'

    def test_raises_value_error_when_source_not_found(self, tmp_path, monkeypatch):
        import pytest
        from lash.plugins.device.core import rename_macro
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        with pytest.raises(ValueError, match="not found"):
            rename_macro('missing', 'new')

    def test_raises_value_error_when_target_exists(self, tmp_path, monkeypatch):
        import pytest
        from lash.plugins.device.helpers import save_macro
        from lash.plugins.device.core import rename_macro
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        save_macro('a', {'name': 'a', 'created_at': '2026-05-15T10:00:00', 'duration': 1.0, 'events': []})
        save_macro('b', {'name': 'b', 'created_at': '2026-05-15T10:00:00', 'duration': 1.0, 'events': []})
        with pytest.raises(ValueError, match="already exists"):
            rename_macro('a', 'b')


class TestDeleteMacro:
    def test_deletes_successfully(self, tmp_path, monkeypatch):
        import pytest
        from lash.plugins.device.helpers import save_macro, load_macro
        from lash.plugins.device.core import delete_macro
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        save_macro('bye', {'name': 'bye', 'created_at': '2026-05-15T10:00:00', 'duration': 1.0, 'events': []})
        delete_macro('bye')
        with pytest.raises(FileNotFoundError):
            load_macro('bye')

    def test_raises_value_error_when_not_found(self, tmp_path, monkeypatch):
        import pytest
        from lash.plugins.device.core import delete_macro
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        with pytest.raises(ValueError, match="not found"):
            delete_macro('missing')


class TestPlayMacro:
    def _make_macro(self, tmp_path, monkeypatch, events):
        from lash.plugins.device.helpers import save_macro
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        save_macro('test', {
            'name': 'test',
            'created_at': '2026-05-15T10:00:00',
            'duration': 1.0,
            'events': events,
        })

    def test_plays_key_down_event(self, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch
        from lash.plugins.device.core import play_macro
        self._make_macro(tmp_path, monkeypatch, [
            {'t': 0.0, 'type': 'key_down', 'key': 'a'},
        ])
        mock_kb_ctrl = MagicMock()
        mock_mouse_ctrl = MagicMock()
        with patch('lash.plugins.device.core._kb_controller', return_value=mock_kb_ctrl), \
             patch('lash.plugins.device.core._mouse_controller', return_value=mock_mouse_ctrl), \
             patch('lash.plugins.device.core.sleep'):
            play_macro('test', speed=1.0, full_speed=False, repeat=1, loop=False)
        mock_kb_ctrl.press.assert_called_once_with('a')

    def test_plays_key_up_event(self, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch
        from lash.plugins.device.core import play_macro
        self._make_macro(tmp_path, monkeypatch, [
            {'t': 0.0, 'type': 'key_up', 'key': 'a'},
        ])
        mock_kb_ctrl = MagicMock()
        mock_mouse_ctrl = MagicMock()
        with patch('lash.plugins.device.core._kb_controller', return_value=mock_kb_ctrl), \
             patch('lash.plugins.device.core._mouse_controller', return_value=mock_mouse_ctrl), \
             patch('lash.plugins.device.core.sleep'):
            play_macro('test', speed=1.0, full_speed=False, repeat=1, loop=False)
        mock_kb_ctrl.release.assert_called_once_with('a')

    def test_plays_mouse_move(self, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch
        from lash.plugins.device.core import play_macro
        self._make_macro(tmp_path, monkeypatch, [
            {'t': 0.0, 'type': 'mouse_move', 'x': 100, 'y': 200},
        ])
        mock_kb_ctrl = MagicMock()
        mock_mouse_ctrl = MagicMock()
        with patch('lash.plugins.device.core._kb_controller', return_value=mock_kb_ctrl), \
             patch('lash.plugins.device.core._mouse_controller', return_value=mock_mouse_ctrl), \
             patch('lash.plugins.device.core.sleep'):
            play_macro('test', speed=1.0, full_speed=False, repeat=1, loop=False)
        assert mock_mouse_ctrl.position == (100, 200)

    def test_plays_mouse_down_and_up(self, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch
        from lash.plugins.device.core import play_macro
        self._make_macro(tmp_path, monkeypatch, [
            {'t': 0.0, 'type': 'mouse_down', 'button': 'left'},
            {'t': 0.1, 'type': 'mouse_up',   'button': 'left'},
        ])
        mock_kb_ctrl = MagicMock()
        mock_mouse_ctrl = MagicMock()
        with patch('lash.plugins.device.core._kb_controller', return_value=mock_kb_ctrl), \
             patch('lash.plugins.device.core._mouse_controller', return_value=mock_mouse_ctrl), \
             patch('lash.plugins.device.core.sleep'):
            play_macro('test', speed=1.0, full_speed=False, repeat=1, loop=False)
        mock_mouse_ctrl.press.assert_called_once()
        mock_mouse_ctrl.release.assert_called_once()

    def test_plays_mouse_scroll(self, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch
        from lash.plugins.device.core import play_macro
        self._make_macro(tmp_path, monkeypatch, [
            {'t': 0.0, 'type': 'mouse_scroll', 'dx': 0, 'dy': -3},
        ])
        mock_kb_ctrl = MagicMock()
        mock_mouse_ctrl = MagicMock()
        with patch('lash.plugins.device.core._kb_controller', return_value=mock_kb_ctrl), \
             patch('lash.plugins.device.core._mouse_controller', return_value=mock_mouse_ctrl), \
             patch('lash.plugins.device.core.sleep'):
            play_macro('test', speed=1.0, full_speed=False, repeat=1, loop=False)
        mock_mouse_ctrl.scroll.assert_called_once_with(0, -3)

    def test_full_speed_skips_sleep(self, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch
        from lash.plugins.device.core import play_macro
        self._make_macro(tmp_path, monkeypatch, [
            {'t': 0.0, 'type': 'key_down', 'key': 'a'},
            {'t': 1.0, 'type': 'key_up',   'key': 'a'},
        ])
        mock_kb_ctrl = MagicMock()
        mock_mouse_ctrl = MagicMock()
        mock_sleep = MagicMock()
        with patch('lash.plugins.device.core._kb_controller', return_value=mock_kb_ctrl), \
             patch('lash.plugins.device.core._mouse_controller', return_value=mock_mouse_ctrl), \
             patch('lash.plugins.device.core.sleep', mock_sleep):
            play_macro('test', speed=1.0, full_speed=True, repeat=1, loop=False)
        for c in mock_sleep.call_args_list:
            assert c.args[0] == 0

    def test_speed_multiplier_scales_delays(self, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch
        from lash.plugins.device.core import play_macro
        self._make_macro(tmp_path, monkeypatch, [
            {'t': 0.0, 'type': 'key_down', 'key': 'a'},
            {'t': 1.0, 'type': 'key_up',   'key': 'a'},
        ])
        mock_kb_ctrl = MagicMock()
        mock_mouse_ctrl = MagicMock()
        sleep_calls = []
        with patch('lash.plugins.device.core._kb_controller', return_value=mock_kb_ctrl), \
             patch('lash.plugins.device.core._mouse_controller', return_value=mock_mouse_ctrl), \
             patch('lash.plugins.device.core.sleep', side_effect=lambda x: sleep_calls.append(x)):
            play_macro('test', speed=2.0, full_speed=False, repeat=1, loop=False)
        assert any(abs(v - 0.5) < 0.001 for v in sleep_calls)

    def test_repeat_n_times(self, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch
        from lash.plugins.device.core import play_macro
        self._make_macro(tmp_path, monkeypatch, [
            {'t': 0.0, 'type': 'key_down', 'key': 'a'},
        ])
        mock_kb_ctrl = MagicMock()
        mock_mouse_ctrl = MagicMock()
        with patch('lash.plugins.device.core._kb_controller', return_value=mock_kb_ctrl), \
             patch('lash.plugins.device.core._mouse_controller', return_value=mock_mouse_ctrl), \
             patch('lash.plugins.device.core.sleep'):
            play_macro('test', speed=1.0, full_speed=False, repeat=3, loop=False)
        assert mock_kb_ctrl.press.call_count == 3

    def test_raises_value_error_when_macro_not_found(self, tmp_path, monkeypatch):
        import pytest
        from lash.plugins.device.core import play_macro
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        with pytest.raises(ValueError, match="not found"):
            play_macro('ghost', speed=1.0, full_speed=False, repeat=1, loop=False)


class TestRecordMacro:
    def test_raises_value_error_when_macro_exists(self, tmp_path, monkeypatch):
        import pytest
        from lash.plugins.device.helpers import save_macro
        from lash.plugins.device.core import record_macro
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        save_macro('exists', {'name': 'exists', 'created_at': '2026-05-15T10:00:00', 'duration': 0.0, 'events': []})
        with pytest.raises(ValueError, match="already exists"):
            record_macro('exists')

    def test_saves_macro_with_events_from_listeners(self, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch
        from lash.plugins.device.core import record_macro
        from lash.plugins.device.helpers import load_macro
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)

        captured_kb_on_press = None

        def fake_kb_listener(**kwargs):
            nonlocal captured_kb_on_press
            captured_kb_on_press = kwargs.get('on_press')
            m = MagicMock()
            m.__enter__ = lambda s: s
            m.__exit__ = MagicMock(return_value=False)
            return m

        def fake_mouse_listener(**kwargs):
            m = MagicMock()
            m.__enter__ = lambda s: s
            m.__exit__ = MagicMock(return_value=False)
            return m

        def fake_stop_event():
            e = MagicMock()
            def wait():
                from unittest.mock import MagicMock as MM
                mock_key = MM()
                mock_key.char = 'a'
                if captured_kb_on_press:
                    captured_kb_on_press(mock_key)
                e.is_set.return_value = True
            e.wait = wait
            e.is_set.return_value = False
            return e

        mock_kb_mod = MagicMock()
        mock_kb_mod.Listener = fake_kb_listener
        mock_kb_mod.Key = MagicMock()

        mock_mouse_mod = MagicMock()
        mock_mouse_mod.Listener = fake_mouse_listener

        with patch.dict('sys.modules', {
                'pynput': MagicMock(),
                'pynput.keyboard': mock_kb_mod,
                'pynput.mouse': mock_mouse_mod,
            }), \
             patch('lash.plugins.device.core.threading') as mock_threading, \
             patch('lash.plugins.device.core.minimize_terminal'), \
             patch('lash.plugins.device.core.time', return_value=0.0):
            mock_threading.Event = fake_stop_event
            record_macro('new_macro')

        data = load_macro('new_macro')
        assert data['name'] == 'new_macro'
        assert len(data['events']) >= 1

    def test_does_not_save_when_no_events(self, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch
        from lash.plugins.device.core import record_macro
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)

        def fake_kb_listener(**kwargs):
            m = MagicMock()
            m.__enter__ = lambda s: s
            m.__exit__ = MagicMock(return_value=False)
            return m

        def fake_mouse_listener(**kwargs):
            m = MagicMock()
            m.__enter__ = lambda s: s
            m.__exit__ = MagicMock(return_value=False)
            return m

        def fake_stop_event():
            e = MagicMock()
            e.wait = lambda: None
            e.is_set.return_value = True
            return e

        mock_kb_mod = MagicMock()
        mock_kb_mod.Listener = fake_kb_listener
        mock_kb_mod.Key = MagicMock()
        mock_mouse_mod = MagicMock()
        mock_mouse_mod.Listener = fake_mouse_listener

        with patch.dict('sys.modules', {
                'pynput': MagicMock(),
                'pynput.keyboard': mock_kb_mod,
                'pynput.mouse': mock_mouse_mod,
            }), \
             patch('lash.plugins.device.core.threading') as mock_threading, \
             patch('lash.plugins.device.core.minimize_terminal'):
            mock_threading.Event = fake_stop_event
            result = record_macro('empty_macro')

        assert result is None
        from lash.plugins.device.helpers import macro_path
        assert not macro_path('empty_macro').exists()


class TestMacroCommand:
    def test_record_flag_calls_record_macro(self, tmp_path, monkeypatch):
        from unittest.mock import patch, MagicMock
        from click.testing import CliRunner
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        with patch('lash.plugins.device.cli.record_macro', return_value={'name': 'x', 'duration': 1.0, 'events': [1]}) as mock_rec, \
             patch('lash.plugins.device.cli.minimize_terminal'):
            from lash.plugins.device.cli import macro
            result = CliRunner().invoke(macro, ['-r', 'x'])
        assert result.exit_code == 0
        mock_rec.assert_called_once_with('x')
        assert "saved" in result.output

    def test_record_existing_macro_shows_error(self, tmp_path, monkeypatch):
        from unittest.mock import patch
        from click.testing import CliRunner
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        with patch('lash.plugins.device.cli.record_macro', side_effect=ValueError("already exists")):
            from lash.plugins.device.cli import macro
            result = CliRunner().invoke(macro, ['-r', 'x'])
        assert result.exit_code != 0
        assert "already exists" in result.output

    def test_play_flag_calls_play_macro(self, tmp_path, monkeypatch):
        from unittest.mock import patch
        from click.testing import CliRunner
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        with patch('lash.plugins.device.cli.play_macro') as mock_play, \
             patch('lash.plugins.device.cli.minimize_terminal'):
            from lash.plugins.device.cli import macro
            result = CliRunner().invoke(macro, ['-p', 'x'])
        assert result.exit_code == 0
        mock_play.assert_called_once_with('x', speed=1.0, full_speed=False, repeat=1, loop=False)

    def test_play_not_found_shows_error(self, tmp_path, monkeypatch):
        from unittest.mock import patch
        from click.testing import CliRunner
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        with patch('lash.plugins.device.cli.play_macro', side_effect=ValueError("not found")):
            from lash.plugins.device.cli import macro
            result = CliRunner().invoke(macro, ['-p', 'ghost'])
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_list_flag_shows_macros(self, tmp_path, monkeypatch):
        from unittest.mock import patch
        from click.testing import CliRunner
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        fake = [{'name': 'login', 'created_at': '2026-05-15T14:32:00', 'duration': 4.8}]
        with patch('lash.plugins.device.cli.list_macros', return_value=fake):
            from lash.plugins.device.cli import macro
            result = CliRunner().invoke(macro, ['-l'])
        assert result.exit_code == 0
        assert 'login' in result.output
        assert '4.8' in result.output

    def test_list_empty_shows_message(self, tmp_path, monkeypatch):
        from unittest.mock import patch
        from click.testing import CliRunner
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        with patch('lash.plugins.device.cli.list_macros', return_value=[]):
            from lash.plugins.device.cli import macro
            result = CliRunner().invoke(macro, ['-l'])
        assert result.exit_code == 0
        assert 'No macros' in result.output

    def test_rename_calls_rename_macro(self, tmp_path, monkeypatch):
        from unittest.mock import patch
        from click.testing import CliRunner
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        with patch('lash.plugins.device.cli.rename_macro') as mock_ren:
            from lash.plugins.device.cli import macro
            result = CliRunner().invoke(macro, ['--rename', 'old', 'new'])
        assert result.exit_code == 0
        mock_ren.assert_called_once_with('old', 'new')
        assert 'renamed' in result.output

    def test_delete_calls_delete_macro(self, tmp_path, monkeypatch):
        from unittest.mock import patch
        from click.testing import CliRunner
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        with patch('lash.plugins.device.cli.delete_macro') as mock_del:
            from lash.plugins.device.cli import macro
            result = CliRunner().invoke(macro, ['-d', 'x'])
        assert result.exit_code == 0
        mock_del.assert_called_once_with('x')
        assert 'deleted' in result.output

    def test_no_action_flag_shows_usage_error(self, tmp_path, monkeypatch):
        from click.testing import CliRunner
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        from lash.plugins.device.cli import macro
        result = CliRunner().invoke(macro, [])
        assert result.exit_code != 0

    def test_speed_and_full_speed_mutually_exclusive(self, tmp_path, monkeypatch):
        from unittest.mock import patch
        from click.testing import CliRunner
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        with patch('lash.plugins.device.cli.play_macro'):
            from lash.plugins.device.cli import macro
            result = CliRunner().invoke(macro, ['-p', 'x', '--speed', '2.0', '--full-speed'])
        assert result.exit_code != 0

    def test_loop_and_n_mutually_exclusive(self, tmp_path, monkeypatch):
        from unittest.mock import patch
        from click.testing import CliRunner
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        with patch('lash.plugins.device.cli.play_macro'):
            from lash.plugins.device.cli import macro
            result = CliRunner().invoke(macro, ['-p', 'x', '--loop', '-n', '3'])
        assert result.exit_code != 0
