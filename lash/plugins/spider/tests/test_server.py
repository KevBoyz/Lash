# pytest lash/plugins/spider/tests/test_server.py
import socket
import pytest
from unittest.mock import MagicMock


class TestProtocol:
    def test_send_recv_round_trip(self):
        from lash.plugins.spider.helpers import send_msg, recv_msg
        a, b = socket.socketpair()
        try:
            data = {"lash": "web"}
            send_msg(a, data)
            result = recv_msg(b)
            assert result == data
        finally:
            a.close()
            b.close()

    def test_round_trip_cmd_payload(self):
        from lash.plugins.spider.helpers import send_msg, recv_msg
        a, b = socket.socketpair()
        try:
            data = {"type": "cmd", "data": "dir /b"}
            send_msg(a, data)
            assert recv_msg(b) == data
        finally:
            a.close()
            b.close()

    def test_round_trip_result_payload(self):
        from lash.plugins.spider.helpers import send_msg, recv_msg
        a, b = socket.socketpair()
        try:
            data = {"type": "result", "data": "file.txt\n", "addr": "192.168.1.5"}
            send_msg(a, data)
            assert recv_msg(b) == data
        finally:
            a.close()
            b.close()

    def test_recv_exact_assembles_partial_reads(self):
        from lash.plugins.spider.helpers import _recv_exact
        mock_sock = MagicMock()
        mock_sock.recv.side_effect = [b"hel", b"lo"]
        assert _recv_exact(mock_sock, 5) == b"hello"

    def test_recv_exact_raises_on_closed_socket(self):
        from lash.plugins.spider.helpers import _recv_exact
        mock_sock = MagicMock()
        mock_sock.recv.return_value = b""
        with pytest.raises(ConnectionError):
            _recv_exact(mock_sock, 4)

    def test_recv_msg_raises_on_closed_socket(self):
        from lash.plugins.spider.helpers import recv_msg
        mock_sock = MagicMock()
        mock_sock.recv.return_value = b""
        with pytest.raises(ConnectionError):
            recv_msg(mock_sock)


class TestWebClient:
    def test_client_receives_and_executes_command(self):
        from unittest.mock import patch
        from lash.plugins.spider.core import run_web_client

        with patch("lash.plugins.spider.core.recv_msg") as mock_recv, \
             patch("lash.plugins.spider.core.send_msg") as mock_send, \
             patch("lash.plugins.spider.core.socket.socket") as mock_socket_cls, \
             patch("lash.plugins.spider.core.subprocess.run") as mock_run:

            mock_run.return_value = MagicMock(stdout="hello\n", stderr="")
            mock_socket_inst = MagicMock()
            mock_socket_cls.return_value.__enter__ = lambda s, *a: mock_socket_inst
            mock_socket_cls.return_value.__exit__ = MagicMock(return_value=False)

            mock_recv.side_effect = [
                {"lash": "web"},
                {"type": "cmd", "data": "echo hello"},
                ConnectionError("done"),
            ]

            run_web_client("127.0.0.1", 9999)

            assert mock_send.called
            sent_result = mock_send.call_args[0][1]
            assert sent_result["type"] == "result"
            assert "hello" in sent_result["data"]

    def test_client_silently_ignores_invalid_welcome(self):
        from lash.plugins.spider.core import run_web_client
        from unittest.mock import patch, MagicMock

        with patch("lash.plugins.spider.core.recv_msg") as mock_recv, \
             patch("lash.plugins.spider.core.socket.socket") as mock_socket_cls:

            mock_socket_inst = MagicMock()
            mock_socket_cls.return_value.__enter__ = lambda s, *a: mock_socket_inst
            mock_socket_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_recv.return_value = {"not_lash": "something"}

            run_web_client("127.0.0.1", 9999)

    def test_port_verify_valid(self):
        from lash.plugins.spider.core import port_verify
        assert port_verify("8080") == 8080

    def test_port_verify_invalid_exits(self):
        from lash.plugins.spider.core import port_verify
        with pytest.raises(ValueError):
            port_verify("notaport")


class TestWebCli:
    def test_no_option_prints_error(self):
        from click.testing import CliRunner
        from lash.plugins.spider.cli import web
        runner = CliRunner()
        result = runner.invoke(web, [])
        assert result.exit_code != 0
        assert "Error" in result.output

    def test_connect_mode_calls_client(self):
        from click.testing import CliRunner
        from unittest.mock import patch
        from lash.plugins.spider.cli import web
        runner = CliRunner()
        with patch("lash.plugins.spider.cli.run_web_client") as mock_client:
            result = runner.invoke(web, ["-c", "127.0.0.1", "8080"])
            mock_client.assert_called_once_with("127.0.0.1", 8080)
            assert result.exit_code == 0

    def test_invalid_port_exits(self):
        from click.testing import CliRunner
        from lash.plugins.spider.cli import web
        runner = CliRunner()
        result = runner.invoke(web, ["-c", "127.0.0.1", "notaport"])
        assert result.exit_code != 0


class TestSeekerPid:
    def test_write_and_read_pid(self, tmp_path):
        from unittest.mock import patch
        pid_file = tmp_path / "seeker.pid"
        with patch("lash.plugins.spider.core.seeker_pid_path", return_value=pid_file):
            from lash.plugins.spider.core import write_pid, read_pid
            write_pid(12345)
            assert read_pid() == 12345

    def test_read_pid_returns_none_when_missing(self, tmp_path):
        from unittest.mock import patch
        pid_file = tmp_path / "seeker.pid"
        with patch("lash.plugins.spider.core.seeker_pid_path", return_value=pid_file):
            from lash.plugins.spider.core import read_pid
            assert read_pid() is None

    def test_read_pid_returns_none_on_corrupt_file(self, tmp_path):
        from unittest.mock import patch
        pid_file = tmp_path / "seeker.pid"
        pid_file.write_text("notanumber")
        with patch("lash.plugins.spider.core.seeker_pid_path", return_value=pid_file):
            from lash.plugins.spider.core import read_pid
            assert read_pid() is None

    def test_is_pid_alive_current_process(self):
        import os
        from lash.plugins.spider.core import is_pid_alive
        assert is_pid_alive(os.getpid()) is True

    def test_is_pid_alive_dead_pid(self):
        from lash.plugins.spider.core import is_pid_alive
        assert is_pid_alive(999999999) is False


class TestSeekerScanLoop:
    def test_scan_once_adds_new_server_to_connected_set(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from lash.plugins.spider.core import _scan_once

        connected = set()
        log_file = tmp_path / "seeker.log"

        with patch("lash.plugins.spider.core.socket.socket") as mock_sock_cls, \
             patch("lash.plugins.spider.core.recv_msg") as mock_recv, \
             patch("lash.plugins.spider.core.seeker_log_path", return_value=log_file), \
             patch("lash.plugins.spider.core._spawn_client") as mock_spawn:

            mock_sock_inst = MagicMock()
            mock_sock_cls.return_value.__enter__ = lambda s, *a: mock_sock_inst
            mock_sock_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_recv.return_value = {"lash": "web"}

            _scan_once(["192.168.1.1"], [8080], connected)

            assert ("192.168.1.1", 8080) in connected
            mock_spawn.assert_called_once_with("web", "192.168.1.1", 8080)

    def test_scan_once_skips_already_connected(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from lash.plugins.spider.core import _scan_once

        connected = {("192.168.1.1", 8080)}

        with patch("lash.plugins.spider.core.socket.socket") as mock_sock_cls, \
             patch("lash.plugins.spider.core._spawn_client") as mock_spawn:

            _scan_once(["192.168.1.1"], [8080], connected)
            mock_spawn.assert_not_called()

    def test_scan_once_skips_connection_refused(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from lash.plugins.spider.core import _scan_once

        connected = set()

        with patch("lash.plugins.spider.core.socket.socket") as mock_sock_cls, \
             patch("lash.plugins.spider.core._spawn_client") as mock_spawn:

            mock_sock_inst = MagicMock()
            mock_sock_inst.connect.side_effect = OSError("refused")
            mock_sock_cls.return_value.__enter__ = lambda s, *a: mock_sock_inst
            mock_sock_cls.return_value.__exit__ = MagicMock(return_value=False)

            _scan_once(["192.168.1.1"], [8080], connected)
            mock_spawn.assert_not_called()
            assert len(connected) == 0

    def test_scan_once_skips_non_lash_server(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from lash.plugins.spider.core import _scan_once

        connected = set()

        with patch("lash.plugins.spider.core.socket.socket") as mock_sock_cls, \
             patch("lash.plugins.spider.core.recv_msg") as mock_recv, \
             patch("lash.plugins.spider.core._spawn_client") as mock_spawn:

            mock_sock_inst = MagicMock()
            mock_sock_cls.return_value.__enter__ = lambda s, *a: mock_sock_inst
            mock_sock_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_recv.return_value = {"not_lash": "something"}

            _scan_once(["192.168.1.1"], [8080], connected)
            mock_spawn.assert_not_called()

    def test_scan_once_writes_to_log(self, tmp_path):
        from unittest.mock import patch, MagicMock
        from lash.plugins.spider.core import _scan_once

        connected = set()
        log_file = tmp_path / "seeker.log"

        with patch("lash.plugins.spider.core.socket.socket") as mock_sock_cls, \
             patch("lash.plugins.spider.core.recv_msg") as mock_recv, \
             patch("lash.plugins.spider.core.seeker_log_path", return_value=log_file), \
             patch("lash.plugins.spider.core._spawn_client"):

            mock_sock_inst = MagicMock()
            mock_sock_cls.return_value.__enter__ = lambda s, *a: mock_sock_inst
            mock_sock_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_recv.return_value = {"lash": "web"}

            _scan_once(["192.168.1.1"], [8080], connected)

            log_content = log_file.read_text()
            assert "web" in log_content
            assert "192.168.1.1" in log_content
            assert "8080" in log_content
            assert "lash web -c 192.168.1.1 8080" in log_content


class TestSeekerDaemon:
    def test_stop_seeker_not_running_when_no_pid_file(self, tmp_path):
        from unittest.mock import patch
        from lash.plugins.spider.core import stop_seeker
        pid_file = tmp_path / "seeker.pid"
        with patch("lash.plugins.spider.core.seeker_pid_path", return_value=pid_file):
            result = stop_seeker()
            assert "not running" in result.lower()

    def test_stop_seeker_not_running_when_pid_dead(self, tmp_path):
        from unittest.mock import patch
        from lash.plugins.spider.core import stop_seeker
        pid_file = tmp_path / "seeker.pid"
        pid_file.write_text("999999999")
        with patch("lash.plugins.spider.core.seeker_pid_path", return_value=pid_file):
            result = stop_seeker()
            assert "not running" in result.lower()
            assert not pid_file.exists()

    def test_stop_seeker_kills_alive_pid(self, tmp_path):
        import os
        from unittest.mock import patch
        from lash.plugins.spider.core import stop_seeker
        pid_file = tmp_path / "seeker.pid"
        pid_file.write_text(str(os.getpid()))
        with patch("lash.plugins.spider.core.seeker_pid_path", return_value=pid_file), \
             patch("os.kill") as mock_kill:
            result = stop_seeker()
            assert "stopped" in result.lower()
            assert not pid_file.exists()
            mock_kill.assert_called()

    def test_spawn_daemon_calls_popen(self):
        from unittest.mock import patch, MagicMock
        from lash.plugins.spider.core import spawn_daemon
        with patch("lash.plugins.spider.core.subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock()
            spawn_daemon("192.168.1.1", "8080", 10)
            mock_popen.assert_called_once()
            call_args = mock_popen.call_args
            cmd = call_args[0][0]
            assert "seeker" in cmd
            assert "--_daemon" in cmd


class TestSeekerCli:
    def test_stop_flag_calls_stop_seeker(self):
        from click.testing import CliRunner
        from unittest.mock import patch
        from lash.plugins.spider.cli import seeker
        runner = CliRunner()
        with patch("lash.plugins.spider.core.stop_seeker", return_value="Seeker stopped (PID: 123)") as mock_stop:
            result = runner.invoke(seeker, ["--stop"])
            assert "stopped" in result.output.lower() or mock_stop.called

    def test_requires_addresses_and_ports_when_not_stopping(self):
        from click.testing import CliRunner
        from lash.plugins.spider.cli import seeker
        runner = CliRunner()
        result = runner.invoke(seeker, [])
        assert result.exit_code != 0

    def test_already_running_warns_user(self):
        from click.testing import CliRunner
        from unittest.mock import patch
        from lash.plugins.spider.cli import seeker
        runner = CliRunner()
        with patch("lash.plugins.spider.core.read_pid", return_value=12345), \
             patch("lash.plugins.spider.core.is_pid_alive", return_value=True):
            result = runner.invoke(seeker, ["192.168.1.1", "8080"])
            assert "already running" in result.output.lower()
            assert result.exit_code != 0

    def test_start_calls_spawn_daemon(self):
        from click.testing import CliRunner
        from unittest.mock import patch, MagicMock
        from lash.plugins.spider.cli import seeker
        runner = CliRunner()
        with patch("lash.plugins.spider.core.read_pid", return_value=None), \
             patch("lash.plugins.spider.core.spawn_daemon") as mock_spawn:
            result = runner.invoke(seeker, ["192.168.1.1", "8080"])
            mock_spawn.assert_called_once_with("192.168.1.1", "8080", 10)
            assert "started" in result.output.lower()
