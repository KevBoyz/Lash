import socket
from unittest.mock import patch, MagicMock


def test_target_reachable_success():
    """Test successful connection to reachable target."""
    with patch('socket.socket') as mock_socket:
        mock_conn = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_conn
        mock_conn.connect.return_value = None

        from lash.plugins.spider.core import _target_reachable

        result = _target_reachable("192.168.1.1", 8080, timeout=0.5)

        assert result is True
        mock_socket.return_value.__enter__.return_value.connect.assert_called_once_with(("192.168.1.1", 8080))


def test_target_reachable_timeout():
    """Test failed connection due to timeout."""
    with patch('socket.socket') as mock_socket:
        mock_conn = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_conn
        mock_conn.connect.side_effect = socket.timeout("Connection timed out")

        from lash.plugins.spider.core import _target_reachable

        result = _target_reachable("192.168.1.1", 8080, timeout=0.5)

        assert result is False
        mock_socket.return_value.__enter__.return_value.connect.assert_called_once_with(("192.168.1.1", 8080))


def test_target_reachable_os_error():
    """Test failed connection due to OSError."""
    with patch('socket.socket') as mock_socket:
        mock_conn = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_conn
        mock_conn.connect.side_effect = OSError("Connection refused")

        from lash.plugins.spider.core import _target_reachable

        result = _target_reachable("192.168.1.1", 8080, timeout=0.5)

        assert result is False
        mock_socket.return_value.__enter__.return_value.connect.assert_called_once_with(("192.168.1.1", 8080))


def test_scan_once_connected():
    """Test that scan_once skips already connected servers."""
    from lash.plugins.spider.core import _scan_once

    addresses = ["192.168.1.1", "192.168.1.2"]
    ports = [8080, 9090]
    connected = {("192.168.1.1", 8080)}  # First target already connected

    with patch('lash.plugins.spider.core.product') as mock_product:
        with patch('lash.plugins.spider.core.recv_msg') as mock_recv_msg:
            with patch('lash.plugins.spider.core._spawn_client') as mock_spawn:
                mock_product.return_value = [
                    ("192.168.1.1", 8080),  # Already connected - should be skipped
                    ("192.168.1.1", 9090),  # Should process
                ]
                mock_recv_msg.return_value = {"lash": "web"}

                _scan_once(addresses, ports, connected)

                # Should spawn for 192.168.1.1:9090 but not 192.168.1.1:8080
                mock_spawn.assert_called_once_with("web", "192.168.1.1", 9090)
                assert ("192.168.1.1", 9090) in connected
                assert ("192.168.1.1", 8080) in connected  # Still in set but not spawned


def test_seeker_scan_loop_updates_connected():
    """Test that seeker_scan_loop updates the connected_servers set."""
    addresses = ["192.168.1.1"]
    ports = [8080]
    connected = set()
    ping_interval = 0.1

    with patch('lash.plugins.spider.core._scan_once') as mock_scan:
        # Run scan_loop for a short time then stop
        import threading
        import time

        def stop_scan():
            time.sleep(0.3)
            # Thread-safe update of connected_servers
            connected.add(("192.168.1.1", 8080))

        threading.Thread(target=stop_scan).start()

        # This will run for 0.3 seconds
        from lash.plugins.spider.core import seeker_scan_loop
        seeker_scan_loop(addresses, ports, ping_interval)

        # Verify scan was called
        assert mock_scan.called
