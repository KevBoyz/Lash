import json
import socket

MSG_HEADER = 4


def send_msg(sock: socket.socket, data: dict) -> None:
    payload = json.dumps(data).encode("utf-8")
    header = len(payload).to_bytes(MSG_HEADER, "big")
    sock.sendall(header + payload)


def recv_msg(sock: socket.socket) -> dict:
    header = _recv_exact(sock, MSG_HEADER)
    length = int.from_bytes(header, "big")
    payload = _recv_exact(sock, length)
    return json.loads(payload.decode("utf-8"))


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Socket closed mid-read")
        data += chunk
    return data
