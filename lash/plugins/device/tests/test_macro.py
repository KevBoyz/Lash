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
