# pytest lash/plugins/server/tests/test_server.py
import socket
import pytest
from unittest.mock import MagicMock


class TestProtocol:
    def test_send_recv_round_trip(self):
        from lash.plugins.server.helpers import send_msg, recv_msg
        a, b = socket.socketpair()
        try:
            data = {"lash": "injection"}
            send_msg(a, data)
            result = recv_msg(b)
            assert result == data
        finally:
            a.close()
            b.close()

    def test_round_trip_cmd_payload(self):
        from lash.plugins.server.helpers import send_msg, recv_msg
        a, b = socket.socketpair()
        try:
            data = {"type": "cmd", "data": "dir /b"}
            send_msg(a, data)
            assert recv_msg(b) == data
        finally:
            a.close()
            b.close()

    def test_round_trip_result_payload(self):
        from lash.plugins.server.helpers import send_msg, recv_msg
        a, b = socket.socketpair()
        try:
            data = {"type": "result", "data": "file.txt\n", "addr": "192.168.1.5"}
            send_msg(a, data)
            assert recv_msg(b) == data
        finally:
            a.close()
            b.close()

    def test_recv_exact_assembles_partial_reads(self):
        from lash.plugins.server.helpers import _recv_exact
        mock_sock = MagicMock()
        mock_sock.recv.side_effect = [b"hel", b"lo"]
        assert _recv_exact(mock_sock, 5) == b"hello"

    def test_recv_exact_raises_on_closed_socket(self):
        from lash.plugins.server.helpers import _recv_exact
        mock_sock = MagicMock()
        mock_sock.recv.return_value = b""
        with pytest.raises(ConnectionError):
            _recv_exact(mock_sock, 4)

    def test_recv_msg_raises_on_closed_socket(self):
        from lash.plugins.server.helpers import recv_msg
        mock_sock = MagicMock()
        mock_sock.recv.return_value = b""
        with pytest.raises(ConnectionError):
            recv_msg(mock_sock)


class TestInjectionClient:
    def test_client_receives_and_executes_command(self):
        from unittest.mock import patch
        from lash.plugins.server.core import run_injection_client

        with patch("lash.plugins.server.core.recv_msg") as mock_recv, \
             patch("lash.plugins.server.core.send_msg") as mock_send, \
             patch("lash.plugins.server.core.socket.socket") as mock_socket_cls, \
             patch("lash.plugins.server.core.subprocess.run") as mock_run:

            mock_run.return_value = MagicMock(stdout="hello\n", stderr="")
            mock_socket_inst = MagicMock()
            mock_socket_cls.return_value.__enter__ = lambda s, *a: mock_socket_inst
            mock_socket_cls.return_value.__exit__ = MagicMock(return_value=False)

            mock_recv.side_effect = [
                {"lash": "injection"},
                {"type": "cmd", "data": "echo hello"},
                ConnectionError("done"),
            ]

            run_injection_client("127.0.0.1", 9999)

            assert mock_send.called
            sent_result = mock_send.call_args[0][1]
            assert sent_result["type"] == "result"
            assert "hello" in sent_result["data"]

    def test_client_silently_ignores_invalid_welcome(self):
        from lash.plugins.server.core import run_injection_client
        from unittest.mock import patch, MagicMock

        with patch("lash.plugins.server.core.recv_msg") as mock_recv, \
             patch("lash.plugins.server.core.socket.socket") as mock_socket_cls:

            mock_socket_inst = MagicMock()
            mock_socket_cls.return_value.__enter__ = lambda s, *a: mock_socket_inst
            mock_socket_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_recv.return_value = {"not_lash": "something"}

            run_injection_client("127.0.0.1", 9999)

    def test_port_verify_valid(self):
        from lash.plugins.server.core import port_verify
        assert port_verify("8080") == 8080

    def test_port_verify_invalid_exits(self):
        from lash.plugins.server.core import port_verify
        with pytest.raises(ValueError):
            port_verify("notaport")


class TestInjectionCli:
    def test_no_option_prints_error(self):
        from click.testing import CliRunner
        from lash.plugins.server.cli import injection
        runner = CliRunner()
        result = runner.invoke(injection, [])
        assert result.exit_code != 0
        assert "Error" in result.output

    def test_connect_mode_calls_client(self):
        from click.testing import CliRunner
        from unittest.mock import patch
        from lash.plugins.server.cli import injection
        runner = CliRunner()
        with patch("lash.plugins.server.cli.run_injection_client") as mock_client:
            result = runner.invoke(injection, ["-c", "127.0.0.1", "8080"])
            mock_client.assert_called_once_with("127.0.0.1", 8080)
            assert result.exit_code == 0

    def test_invalid_port_exits(self):
        from click.testing import CliRunner
        from lash.plugins.server.cli import injection
        runner = CliRunner()
        result = runner.invoke(injection, ["-c", "127.0.0.1", "notaport"])
        assert result.exit_code != 0


class TestSeekerPid:
    def test_write_and_read_pid(self, tmp_path):
        from unittest.mock import patch
        pid_file = tmp_path / "seeker.pid"
        with patch("lash.plugins.server.core.seeker_pid_path", return_value=pid_file):
            from lash.plugins.server.core import write_pid, read_pid
            write_pid(12345)
            assert read_pid() == 12345

    def test_read_pid_returns_none_when_missing(self, tmp_path):
        from unittest.mock import patch
        pid_file = tmp_path / "seeker.pid"
        with patch("lash.plugins.server.core.seeker_pid_path", return_value=pid_file):
            from lash.plugins.server.core import read_pid
            assert read_pid() is None

    def test_read_pid_returns_none_on_corrupt_file(self, tmp_path):
        from unittest.mock import patch
        pid_file = tmp_path / "seeker.pid"
        pid_file.write_text("notanumber")
        with patch("lash.plugins.server.core.seeker_pid_path", return_value=pid_file):
            from lash.plugins.server.core import read_pid
            assert read_pid() is None

    def test_is_pid_alive_current_process(self):
        import os
        from lash.plugins.server.core import is_pid_alive
        assert is_pid_alive(os.getpid()) is True

    def test_is_pid_alive_dead_pid(self):
        from lash.plugins.server.core import is_pid_alive
        assert is_pid_alive(999999999) is False
