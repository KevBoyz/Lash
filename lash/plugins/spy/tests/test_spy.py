# pytest lash/plugins/spy/tests/test_spy.py
import os
import pytest


class TestPortVerify:
    def test_valid_port(self):
        from lash.plugins.spy.core import port_verify
        assert port_verify("8080") == 8080

    def test_valid_port_returns_int(self):
        from lash.plugins.spy.core import port_verify
        result = port_verify("4254")
        assert isinstance(result, int)

    def test_invalid_port_exits(self):
        from lash.plugins.spy.core import port_verify
        with pytest.raises(SystemExit):
            port_verify("notaport")

    def test_invalid_port_float_string_exits(self):
        from lash.plugins.spy.core import port_verify
        with pytest.raises(SystemExit):
            port_verify("80.5")


class TestKeyUp:
    def test_f3_returns_false(self):
        from lash.plugins.spy.core import key_up
        from pynput.keyboard import Key
        result = key_up(Key.f3)
        assert result is False

    def test_other_key_returns_none(self):
        from lash.plugins.spy.core import key_up
        from pynput.keyboard import Key
        result = key_up(Key.enter)
        assert result is None

    def test_letter_key_returns_none(self):
        from lash.plugins.spy.core import key_up
        from pynput.keyboard import Key
        result = key_up(Key.space)
        assert result is None


class TestInjectionClientMsg:
    def test_returns_table(self):
        from lash.plugins.spy.core import injection_client_msg
        from rich.table import Table
        result = injection_client_msg()
        assert isinstance(result, Table)

    def test_table_has_rows(self):
        from lash.plugins.spy.core import injection_client_msg
        result = injection_client_msg()
        assert result.row_count > 0

    def test_table_has_two_columns(self):
        from lash.plugins.spy.core import injection_client_msg
        result = injection_client_msg()
        assert result.column_count == 2

    def test_table_contains_chdir_row(self):
        from lash.plugins.spy.core import injection_client_msg
        from io import StringIO
        from rich.console import Console
        result = injection_client_msg()
        buf = StringIO()
        console = Console(file=buf, highlight=False)
        console.print(result)
        assert '-chdir' in buf.getvalue()

    def test_table_contains_kill_row(self):
        from lash.plugins.spy.core import injection_client_msg
        from io import StringIO
        from rich.console import Console
        result = injection_client_msg()
        buf = StringIO()
        console = Console(file=buf, highlight=False)
        console.print(result)
        assert '-kill' in buf.getvalue()


class TestKeyDown:
    def test_writes_char_to_file(self, tmp_path):
        from lash.plugins.spy.core import key_down
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
        from lash.plugins.spy.core import key_down
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
        from lash.plugins.spy.core import key_down
        from pynput.keyboard import Key
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Key.space has no .char attribute → raises AttributeError inside key_down
            key_down(Key.space)
            log_path = tmp_path / 'Keylogger.txt'
            assert log_path.read_text() == ' '
        finally:
            os.chdir(original_dir)

    def test_writes_backspace_marker(self, tmp_path):
        from lash.plugins.spy.core import key_down
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
        from lash.plugins.spy.core import key_down
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
        from lash.plugins.spy.core import key_down
        from pynput.keyboard import Key
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Key.f1 is not handled by any specific branch → falls to generic <key>
            key_down(Key.f1)
            log_path = tmp_path / 'Keylogger.txt'
            content = log_path.read_text()
            assert content.startswith(' <') and content.endswith('> ')
        finally:
            os.chdir(original_dir)


class TestCryptCommand:
    def test_encrypt_file_changes_content(self):
        from click.testing import CliRunner
        from lash.plugins.spy.cli import crypt
        runner = CliRunner()
        original_content = b'hello world'
        key = 'kvzis1@7y602qsxA'  # exactly 16 chars
        with runner.isolated_filesystem():
            with open('secret.txt', 'wb') as f:
                f.write(original_content)
            result = runner.invoke(crypt, ['secret.txt', key])
            assert result.exit_code == 0
            with open('secret.txt', 'rb') as f:
                encrypted = f.read()
            assert encrypted != original_content

    def test_decrypt_roundtrip(self):
        from click.testing import CliRunner
        from lash.plugins.spy.cli import crypt
        runner = CliRunner()
        original_content = b'roundtrip test data'
        key = 'kvzis1@7y602qsxA'  # exactly 16 chars
        with runner.isolated_filesystem():
            with open('data.txt', 'wb') as f:
                f.write(original_content)
            # encrypt
            result = runner.invoke(crypt, ['data.txt', key])
            assert result.exit_code == 0
            # decrypt
            result = runner.invoke(crypt, ['data.txt', key, '-dc'])
            assert result.exit_code == 0
            with open('data.txt', 'rb') as f:
                restored = f.read()
            assert restored == original_content

    def test_encrypt_verbose_prints_message(self):
        from click.testing import CliRunner
        from lash.plugins.spy.cli import crypt
        runner = CliRunner()
        key = 'kvzis1@7y602qsxA'
        with runner.isolated_filesystem():
            with open('note.txt', 'wb') as f:
                f.write(b'some text')
            result = runner.invoke(crypt, ['note.txt', key, '-v'])
            assert result.exit_code == 0
            assert 'encrypted' in result.output.lower()

    def test_decrypt_verbose_prints_message(self):
        from click.testing import CliRunner
        from lash.plugins.spy.cli import crypt
        runner = CliRunner()
        key = 'kvzis1@7y602qsxA'
        with runner.isolated_filesystem():
            with open('note.txt', 'wb') as f:
                f.write(b'some text')
            runner.invoke(crypt, ['note.txt', key])
            result = runner.invoke(crypt, ['note.txt', key, '-dc', '-v'])
            assert result.exit_code == 0
            assert 'decrypted' in result.output.lower()

    def test_encrypt_folder_with_cl_flag(self):
        from click.testing import CliRunner
        from lash.plugins.spy.cli import crypt
        runner = CliRunner()
        key = 'kvzis1@7y602qsxA'
        original_a = b'file alpha content'
        original_b = b'file beta content'
        with runner.isolated_filesystem():
            os.makedirs('mydir')
            with open(os.path.join('mydir', 'a.txt'), 'wb') as f:
                f.write(original_a)
            with open(os.path.join('mydir', 'b.txt'), 'wb') as f:
                f.write(original_b)
            result = runner.invoke(crypt, ['mydir', key, '-cl'])
            assert result.exit_code == 0
            with open(os.path.join('mydir', 'a.txt'), 'rb') as f:
                assert f.read() != original_a
            with open(os.path.join('mydir', 'b.txt'), 'rb') as f:
                assert f.read() != original_b

    @pytest.mark.skip(reason=(
        "keyboard command starts a blocking pynput Listener — "
        "cannot be tested without a real display/input device."
    ))
    def test_keyboard_command_skipped(self):
        pass

    @pytest.mark.skip(reason=(
        "injection command opens real network sockets and blocks in an infinite loop — "
        "not testable without live socket infrastructure."
    ))
    def test_injection_command_skipped(self):
        pass
