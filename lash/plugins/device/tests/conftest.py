import sys
import pytest
from enum import Enum, auto
from unittest.mock import MagicMock


class _Key(Enum):
    f1 = auto()
    f2 = auto()
    f3 = auto()
    space = auto()
    backspace = auto()
    shift = auto()
    ctrl_l = auto()
    enter = auto()
    tab = auto()
    esc = auto()


@pytest.fixture(autouse=True)
def mock_pynput(monkeypatch):
    mock_keyboard = MagicMock()
    mock_keyboard.Key = _Key
    mock_keyboard.Listener = MagicMock
    mock_keyboard.Controller = MagicMock

    mock_mouse = MagicMock()

    mock_pynput_mod = MagicMock()
    mock_pynput_mod.keyboard = mock_keyboard
    mock_pynput_mod.mouse = mock_mouse

    monkeypatch.setitem(sys.modules, 'pynput', mock_pynput_mod)
    monkeypatch.setitem(sys.modules, 'pynput.keyboard', mock_keyboard)
    monkeypatch.setitem(sys.modules, 'pynput.mouse', mock_mouse)
