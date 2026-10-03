"""Keyboard regression tests; no real keys are injected into the desktop."""

import pytest


@pytest.fixture
def kb():
    try:
        import pynput.keyboard as keyboard
    except ImportError as exc:
        pytest.skip(f"pynput.keyboard unavailable: {exc}")
    return keyboard


@pytest.fixture
def windows_inputs(kb, monkeypatch):
    import ctypes
    import sys

    if sys.platform != "win32":
        pytest.skip("Windows SendInput regression")
    from pynput.keyboard import _win32

    sent = []

    def capture(count, inputs, size):
        values = ctypes.cast(inputs, ctypes.POINTER(_win32.INPUT))
        for index in range(count):
            key = values[index].value.ki
            sent.append((key.wVk, key.wScan, key.dwFlags))
        return count

    monkeypatch.setattr(_win32, "SendInput", capture)
    return sent


@pytest.fixture
def playback(monkeypatch):
    import threading
    from unittest.mock import Mock
    from lash.plugins.macro import core

    stop, done, watcher = threading.Event(), threading.Event(), Mock()
    keyboard, mouse = Mock(), Mock()
    monkeypatch.setattr(core, "_setup_f3_watcher", lambda: (stop, done, watcher))
    monkeypatch.setattr(core, "_kb_controller", lambda: keyboard)
    monkeypatch.setattr(core, "_mouse_controller", lambda: mouse)
    monkeypatch.setattr(core, "sleep", lambda _: None)
    return stop, done, watcher, keyboard


class TestKeyIdentity:
    @pytest.mark.parametrize("char", ["v", "V", "\x16", None])
    def test_serialization_keeps_virtual_key_independent_of_modifiers(self, char):
        from types import SimpleNamespace
        from lash.plugins.macro.helpers import serialize_key

        key = SimpleNamespace(vk=0x56, char=char)
        assert serialize_key(key) == {"vk": 0x56}

    def test_vk_zero_is_not_discarded(self):
        from types import SimpleNamespace
        from lash.plugins.macro.helpers import serialize_key

        assert serialize_key(SimpleNamespace(vk=0, char="a")) == {"vk": 0}

    def test_virtual_key_roundtrip_through_json(self, kb):
        import json
        from lash.plugins.macro.helpers import serialize_key, deserialize_key

        data = json.loads(json.dumps(serialize_key(kb.KeyCode(vk=86, char="V"))))
        key = deserialize_key(data)
        assert key.vk == 86
        assert key.char is None

    def test_named_keys_keep_their_sides_and_extended_flags(self, kb):
        from lash.plugins.macro.helpers import serialize_key, deserialize_key

        for key in kb.Key:
            assert deserialize_key(serialize_key(key)) == key

    def test_windows_scan_code_and_flags_survive_json(self, windows_inputs, kb):
        import json
        from lash.plugins.macro.helpers import serialize_key, deserialize_key

        key = kb.KeyCode(vk=0x6F, _scan=0x35, _flags=1)
        saved = json.loads(json.dumps(serialize_key(key)))
        kb.Controller().press(deserialize_key(saved))
        assert windows_inputs == [(0x6F, 0x35, 1)]

    def test_unicode_without_virtual_key_keeps_text_fallback(self, kb):
        from lash.plugins.macro.helpers import serialize_key, deserialize_key

        assert deserialize_key(serialize_key(kb.KeyCode.from_char("\u2603"))) == "\u2603"

    @pytest.mark.parametrize("code", range(1, 27))
    def test_legacy_ctrl_letters_are_recovered(self, code):
        from lash.plugins.macro.helpers import deserialize_key

        assert deserialize_key(chr(code)) == chr(ord("a") + code - 1)

    def test_legacy_named_tab_and_enter_are_not_ctrl_letters(self, kb):
        from lash.plugins.macro.helpers import deserialize_key

        assert deserialize_key("Key.tab") == kb.Key.tab
        assert deserialize_key("Key.enter") == kb.Key.enter


class TestWindowsShortcutPlayback:
    def test_all_modifier_combinations_send_physical_key_events(
        self, windows_inputs, kb, monkeypatch
    ):
        import itertools
        import threading
        from lash.plugins.macro import core
        from lash.plugins.macro.helpers import serialize_key

        monkeypatch.setattr(core, "sleep", lambda _: None)
        modifiers = [kb.Key.ctrl_l, kb.Key.shift, kb.Key.alt_l, kb.Key.cmd]
        # Letters, digits, punctuation, numpad, and keys without a character.
        codes = [*range(0x41, 0x5B), *range(0x30, 0x3A),
                 *range(0x60, 0x70), *range(0xBA, 0xC1), 0xDB, 0xDC, 0xDD, 0xDE]
        controller = kb.Controller()
        for size in range(1, len(modifiers) + 1):
            for combo in itertools.combinations(modifiers, size):
                for vk in codes:
                    # Even a misleading character must never replace vk.
                    key = kb.KeyCode(vk=vk, char="\x16")
                    keys = [*combo, key]
                    events = [
                        {"t": 0, "type": "key_down", "key": serialize_key(k)}
                        for k in keys
                    ] + [
                        {"t": 0, "type": "key_up", "key": serialize_key(k)}
                        for k in reversed(keys)
                    ]
                    windows_inputs.clear()
                    core._run_macro_once(events, 0, threading.Event(), controller, None)
                    expected = [k.value.vk for k in combo] + [vk]
                    assert [v for v, _, _ in windows_inputs] == expected + expected[::-1]
                    assert all(flags & 4 == 0 for _, _, flags in windows_inputs)
                    assert all(flags & 2 == 0 for _, _, flags in windows_inputs[:len(keys)])
                    assert all(flags & 2 for _, _, flags in windows_inputs[len(keys):])

    @pytest.mark.parametrize("special", [
        "tab", "enter", "esc", "delete", "insert", "home", "end",
        "left", "right", "up", "down", "page_up", "page_down", "f1", "f12",
        "media_volume_up", "space", "backspace",
    ])
    def test_right_modifiers_with_special_keys(self, windows_inputs, kb, special):
        from lash.plugins.macro.core import _dispatch_event
        from lash.plugins.macro.helpers import serialize_key

        held = []
        controller = kb.Controller()
        keys = [kb.Key.ctrl_r, kb.Key.alt_r, kb.Key.shift_r, getattr(kb.Key, special)]
        for event_type, sequence in [("key_down", keys), ("key_up", keys[::-1])]:
            for key in sequence:
                _dispatch_event({"type": event_type, "key": serialize_key(key)},
                                controller, None, held)
        assert not held
        expected = [key.value.vk for key in keys]
        assert [v for v, _, _ in windows_inputs] == expected + expected[::-1]
        assert windows_inputs[0][2] & 1  # Extended right Ctrl.
        assert windows_inputs[1][2] & 1  # Extended right Alt / AltGr.

    @pytest.mark.parametrize("legacy_key", ["\x16", "V", "v", "+"])
    def test_legacy_shortcut_releases_same_key_after_modifiers(
        self, windows_inputs, kb, legacy_key
    ):
        from lash.plugins.macro.core import _dispatch_event

        controller, held = kb.Controller(), []
        events = [
            ("key_down", "Key.ctrl_l"), ("key_down", "Key.shift"),
            ("key_down", legacy_key), ("key_up", "Key.shift"),
            ("key_up", "Key.ctrl_l"),
            ("key_up", "v" if legacy_key in ("\x16", "V") else legacy_key),
        ]
        for event_type, key in events:
            _dispatch_event({"type": event_type, "key": key}, controller, None, held)
        assert not held
        assert len(windows_inputs) == 6
        assert windows_inputs[2][0] == windows_inputs[-1][0] != 0
        assert all(flags & 4 == 0 for _, _, flags in windows_inputs)


class TestShortcutRecording:
    def test_record_save_load_and_replay_ctrl_v(self, tmp_path, monkeypatch, kb):
        import threading
        from pathlib import Path
        from unittest.mock import Mock
        import pynput.mouse as mouse
        from lash.plugins.macro import core
        from lash.plugins.macro.helpers import load_macro

        callbacks = {}

        class KeyboardListener:
            def __init__(self, **kwargs):
                callbacks.update(kwargs)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        class MouseListener(KeyboardListener):
            def __init__(self, **kwargs):
                pass

            def __enter__(self):
                callbacks["on_press"](kb.Key.ctrl_l)
                callbacks["on_press"](kb.KeyCode(vk=86, char="\x16"))
                callbacks["on_release"](kb.Key.ctrl_l)
                callbacks["on_release"](kb.KeyCode(vk=86, char="v"))
                callbacks["on_press"](kb.Key.f3)
                callbacks["on_release"](kb.Key.f3)
                # Queued callbacks after F3 must not extend the recording.
                callbacks["on_press"](kb.KeyCode(vk=65, char="a"))
                return self

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setattr(kb, "Listener", KeyboardListener)
        monkeypatch.setattr(mouse, "Listener", MouseListener)
        monkeypatch.setattr(core, "_mouse_controller", Mock)
        monkeypatch.setattr(core, "minimize_terminal", lambda: None)
        monkeypatch.setattr(core, "sleep", lambda _: None)
        core.record_macro("paste")
        events = load_macro("paste")["events"]
        assert [event["key"] for event in events] == [
            "Key.ctrl_l", {"vk": 86}, "Key.ctrl_l", {"vk": 86},
        ]
        controller = Mock()
        core._run_macro_once(events, 0, threading.Event(), controller, None)
        from unittest.mock import call

        assert controller.method_calls == [
            call.press(kb.Key.ctrl_l), call.press(kb.KeyCode.from_vk(86)),
            call.release(kb.Key.ctrl_l), call.release(kb.KeyCode.from_vk(86)),
        ]


class TestPlaybackCleanup:
    @pytest.mark.parametrize("reason", ["end", "f3", "error", "interrupt"])
    def test_releases_held_keys_and_stops_watcher(self, playback, monkeypatch, kb, reason):
        from unittest.mock import call
        from lash.plugins.macro import core

        stop, done, watcher, controller = playback
        monkeypatch.setattr(core, "_load_macro_data", lambda _: {"events": [
            {"t": 0, "type": "key_down", "key": "Key.ctrl_l"},
            {"t": 0, "type": "key_down", "key": {"vk": 86}},
        ]})

        def press(key):
            if key == kb.Key.ctrl_l:
                return
            if reason == "f3":
                stop.set()
            elif reason == "error":
                raise RuntimeError("send failed")
            elif reason == "interrupt":
                raise KeyboardInterrupt

        controller.press.side_effect = press
        if reason in ("error", "interrupt"):
            error = RuntimeError if reason == "error" else KeyboardInterrupt
            with pytest.raises(error):
                core.play_macro("test", 1, True, 1, False)
        else:
            assert core.play_macro("test", 1, True, 1, False) == (reason == "f3")
        assert controller.release.call_args_list == [
            call(kb.KeyCode.from_vk(86)), call(kb.Key.ctrl_l),
        ]
        assert done.is_set()
        watcher.join.assert_called_once()

    def test_repeated_key_down_is_released_once_per_iteration(self, playback, monkeypatch):
        from unittest.mock import call
        from lash.plugins.macro import core

        controller = playback[-1]
        monkeypatch.setattr(core, "_load_macro_data", lambda _: {"events": [
            {"t": 0, "type": "key_down", "key": "a"},
            {"t": 0, "type": "key_down", "key": "a"},
        ]})
        core.play_macro("test", 1, True, 2, False)
        assert controller.method_calls == [
            call.press("a"), call.press("a"), call.release("a"),
            call.press("a"), call.press("a"), call.release("a"),
        ]

    def test_release_failure_does_not_leave_other_modifiers_held(self, playback, monkeypatch, kb):
        from unittest.mock import call
        from lash.plugins.macro import core

        _, done, _, controller = playback
        monkeypatch.setattr(core, "_load_macro_data", lambda _: {"events": [
            {"t": 0, "type": "key_down", "key": "Key.ctrl_l"},
            {"t": 0, "type": "key_down", "key": {"vk": 86}},
        ]})
        controller.release.side_effect = [RuntimeError("release failed"), None]
        with pytest.raises(RuntimeError, match="release failed"):
            core.play_macro("test", 1, True, 1, False)
        assert controller.release.call_args_list == [
            call(kb.KeyCode.from_vk(86)), call(kb.Key.ctrl_l),
        ]
        assert done.is_set()
