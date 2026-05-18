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
