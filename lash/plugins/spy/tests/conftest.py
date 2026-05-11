import sys
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


_mock_keyboard = MagicMock()
_mock_keyboard.Key = _Key
_mock_keyboard.Listener = MagicMock

_mock_pynput = MagicMock()
_mock_pynput.keyboard = _mock_keyboard

sys.modules['pynput'] = _mock_pynput
sys.modules['pynput.keyboard'] = _mock_keyboard
