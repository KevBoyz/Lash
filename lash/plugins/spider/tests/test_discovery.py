import pytest


class TestDiscovery:
    def test_udp_round_trip_and_responder_cleanup(self):
        import socket
        from lash.plugins.spider.core import (
            discover_servers, discovery_responder,
        )

        with discovery_responder(54321, discovery_port=0) as udp_port:
            found = discover_servers(
                0.1, discovery_port=udp_port,
                broadcast_address="127.0.0.1")
        assert found == [("127.0.0.1", 54321)]
        # Shutdown releases the UDP port, including on Windows.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(("0.0.0.0", udp_port))

    def test_responder_survives_invalid_queries(self):
        import socket
        from lash.plugins.spider.core import (
            discover_servers, discovery_responder,
        )

        with discovery_responder(54321, discovery_port=0) as udp_port:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                for raw in [b"not json", b"[]", b"null", b'{}', b'\xff']:
                    sock.sendto(raw, ("127.0.0.1", udp_port))
            assert discover_servers(
                0.1, discovery_port=udp_port,
                broadcast_address="127.0.0.1") == [("127.0.0.1", 54321)]

    def test_filters_replies_and_preserves_endpoint_pairs(self):
        import json
        import socket
        from unittest.mock import patch
        from lash.plugins.spider.core import discover_servers

        valid = {"lash": "web", "version": 1, "nonce": "query", "port": 8080}
        replies = [
            (b"not-json", ("192.168.1.9", 45873)),
            (b"null", ("192.168.1.9", 45873)),
            (b"[]", ("192.168.1.9", 45873)),
        ]
        for changes in [
            {"nonce": "old"}, {"version": 2}, {"lash": "other"},
            {"port": 0}, {"port": 65536}, {"port": True}, {"port": "8080"},
        ]:
            replies.append((json.dumps(valid | changes).encode(),
                            ("192.168.1.9", 45873)))
        replies.extend([
            (json.dumps(valid).encode(), ("192.168.1.10", 45873)),
            (json.dumps(valid).encode(), ("192.168.1.10", 45873)),
            (json.dumps(valid | {"port": 9090}).encode(),
             ("192.168.1.11", 45873)),
            socket.timeout(),
        ])
        with patch("lash.plugins.spider.core.socket.socket") as factory, \
                patch("lash.plugins.spider.core.secrets.token_hex",
                      return_value="query"):
            sock = factory.return_value.__enter__.return_value
            sock.recvfrom.side_effect = replies
            found = discover_servers()
        assert found == [("192.168.1.10", 8080), ("192.168.1.11", 9090)]
        sock.setsockopt.assert_called_once_with(
            socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        assert sock.sendto.call_args.args[1] == ("255.255.255.255", 45873)

    def test_discovery_has_deadline_even_with_unrelated_traffic(self):
        from unittest.mock import patch
        from lash.plugins.spider.core import discover_servers

        with patch("lash.plugins.spider.core.socket.socket") as factory, \
                patch("lash.plugins.spider.core.time.monotonic",
                      side_effect=[0, 0.1, 1.1]):
            sock = factory.return_value.__enter__.return_value
            sock.recvfrom.return_value = (b"{}", ("192.168.1.2", 45873))
            assert discover_servers(timeout=1) == []
            sock.recvfrom.assert_called_once()


class TestAutomaticSeeker:
    def test_discovery_connects_once_and_reconnects_after_client_exit(
        self, tmp_path,
    ):
        from unittest.mock import MagicMock, patch
        from lash.plugins.spider.core import seeker_scan_loop

        process = MagicMock()
        process.poll.side_effect = [None, 0]
        with patch("lash.plugins.spider.core.discover_servers",
                   return_value=[("192.168.1.2", 8080)]) as discover, \
                patch("lash.plugins.spider.core.socket.socket"), \
                patch("lash.plugins.spider.core.recv_msg",
                      return_value={"lash": "web"}), \
                patch("lash.plugins.spider.core._spawn_client",
                      return_value=process) as spawn, \
                patch("lash.plugins.spider.core.seeker_log_path",
                      return_value=tmp_path / "seeker.log"), \
                patch("lash.plugins.spider.core.time.sleep",
                      side_effect=[None, None, KeyboardInterrupt]):
            with pytest.raises(KeyboardInterrupt):
                seeker_scan_loop(None, None, 10)
        assert discover.call_count == 3
        assert spawn.call_count == 2

    def test_network_failure_is_retried(self):
        from unittest.mock import patch
        from lash.plugins.spider.core import seeker_scan_loop

        with patch("lash.plugins.spider.core.discover_servers",
                   side_effect=[OSError("network down"), []]) as discover, \
                patch("lash.plugins.spider.core.time.sleep",
                      side_effect=[None, KeyboardInterrupt]):
            with pytest.raises(KeyboardInterrupt):
                seeker_scan_loop(None, None, 10)
        assert discover.call_count == 2

    def test_scan_keeps_handshake_timeout_and_ignores_silent_servers(self):
        import socket
        from unittest.mock import patch
        from lash.plugins.spider.core import _scan_once

        with patch("lash.plugins.spider.core.socket.socket") as factory, \
                patch("lash.plugins.spider.core.recv_msg",
                      side_effect=socket.timeout()), \
                patch("lash.plugins.spider.core._spawn_client") as spawn:
            _scan_once(["192.168.1.2"], [8080], {})
        factory.return_value.__enter__.return_value.settimeout\
            .assert_called_once_with(0.5)
        spawn.assert_not_called()

    @pytest.mark.parametrize("greeting", [None, [], {"lash": "unknown"}])
    def test_scan_ignores_unrecognized_greetings(self, greeting):
        from unittest.mock import patch
        from lash.plugins.spider.core import _scan_once

        with patch("lash.plugins.spider.core.socket.socket"), \
                patch("lash.plugins.spider.core.recv_msg",
                      return_value=greeting), \
                patch("lash.plugins.spider.core._spawn_client") as spawn:
            _scan_once(["192.168.1.2"], [8080], {})
        spawn.assert_not_called()

    def test_spawn_failure_does_not_mark_server_as_connected(self):
        from unittest.mock import patch
        from lash.plugins.spider.core import _scan_once

        connected = {}
        with patch("lash.plugins.spider.core.socket.socket"), \
                patch("lash.plugins.spider.core.recv_msg",
                      return_value={"lash": "web"}), \
                patch("lash.plugins.spider.core._spawn_client",
                      side_effect=OSError("cannot launch")):
            _scan_once(["192.168.1.2"], [8080], connected)
        assert connected == {}

    def test_auto_daemon_argv_has_no_placeholder_addresses(self):
        import sys
        from unittest.mock import patch
        from lash.plugins.spider.core import spawn_daemon

        with patch("lash.plugins.spider.core.subprocess.Popen") as spawn:
            spawn_daemon(None, None, 5)
        assert spawn.call_args.args[0] == [
            sys.executable, "-m", "lash", "spider", "seeker",
            "--ping", "5", "--_daemon",
        ]

    def test_daemon_removes_pid_after_failure(self, tmp_path):
        from unittest.mock import patch
        from lash.plugins.spider.core import run_seeker_daemon

        pid_path = tmp_path / "seeker.pid"
        with patch("lash.plugins.spider.core.seeker_pid_path",
                   return_value=pid_path), \
                patch("lash.plugins.spider.core.seeker_scan_loop",
                      side_effect=RuntimeError("stopped")):
            with pytest.raises(RuntimeError, match="stopped"):
                run_seeker_daemon(None, None, 10)
        assert not pid_path.exists()


class TestHandshake:
    def test_rejects_oversized_greeting_before_reading_payload(self):
        from unittest.mock import MagicMock
        from lash.plugins.spider.helpers import recv_msg

        sock = MagicMock()
        sock.recv.return_value = (1000000).to_bytes(4, "big")
        with pytest.raises(ValueError, match="exceeds"):
            recv_msg(sock, max_size=4096)
        sock.recv.assert_called_once_with(4)
